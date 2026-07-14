import os
import argparse
import sys
from isaacsim import SimulationApp

# Mantener la instancia global activa
kit_instance = None

def inicializar_omni_headless():
    global kit_instance
    # Workaround for hotkeys crash in windowed mode
    if "--disable" not in sys.argv:
        sys.argv.extend(["--disable", "omni.kit.hotkeys.core"])
    kit_instance = SimulationApp({"headless": True})

def ejecutar_replicator_randomization(usd_path, hdri_dir, output_dataset_dir):
    import omni.replicator.core as rep
    from pxr import Usd, UsdGeom

    if not os.path.exists(usd_path):
        print(f"Error: El archivo USD no existe en {usd_path}")
        return
    if not os.path.exists(hdri_dir):
        print(f"Error: La ruta de HDRIs no existe en {hdri_dir}")
        return

    # 1. Filtrar HDRIs válidos ignorando archivos .rat
    hdri_files = [
        os.path.join(hdri_dir, f).replace("\\", "/")
        for f in os.listdir(hdri_dir)
        if f.lower().endswith(('.exr', '.hdr')) and not f.lower().endswith('.rat')
    ]

    if not hdri_files:
        print(f"Error: No se encontraron archivos HDRIs válidos en {hdri_dir}")
        return

    # 2. Abrir el Stage directamente en el contexto de Omniverse
    import omni.usd
    omni.usd.get_context().open_stage(usd_path)
    kit_instance.update()
    stage = omni.usd.get_context().get_stage()
    world_prim = stage.GetPrimAtPath("/World")
    
    nombres_objetos = []
    if world_prim.IsValid():
        for child in world_prim.GetChildren():
            # Filtrar solo elementos de tipo Xform o Mesh, ignorando la cámara, luces preexistentes o Looks
            if child.GetName() not in ["Looks", "Camera"] and (child.IsA(UsdGeom.Xform) or child.IsA(UsdGeom.Mesh)):
                nombres_objetos.append(child.GetName())

    HDRI_PATHS = [
        r"C:\Users\bruni\Documents\HoudiniJOb\hdris\dikhololo_night_4k.exr",
        r"C:\Users\bruni\Documents\HoudiniJOb\hdris\ferndale_studio_02_4k.exr",
        r"C:\Users\bruni\Documents\HoudiniJOb\hdris\moonless_golf_4k.exr",
        r"C:\Users\bruni\Documents\HoudiniJOb\hdris\pool_4k.exr",
        r"C:\Users\bruni\Documents\HoudiniJOb\hdris\poolbeg_4k.exr",
        r"C:\Users\bruni\Documents\HoudiniJOb\hdris\satara_night_4k.exr",
        r"C:\Users\bruni\Documents\HoudiniJOb\hdris\snowy_forest_path_01_4k.exr",
        r"C:\Users\bruni\Documents\HoudiniJOb\hdris\suburban_garden_4k.exr",
        r"C:\Users\bruni\Documents\HoudiniJOb\hdris\wooden_studio_13_4k.exr",
    ]

    # 3.5 Crear el Domo de Iluminación manualmente en USD (fuera de Replicator)
    # Esto evita el bug donde rep.create.light lo mete en un DomeLight_Xform que rompe el render
    from pxr import UsdLux
    dome_light_path = "/World/HDRI_DomeLight"
    dome_usd = UsdLux.DomeLight.Define(stage, dome_light_path)
    dome_usd.CreateIntensityAttr(1000.0)

    # Re-apply semantics natively via Replicator API to ensure BBoxes are generated
    for nombre in nombres_objetos:
        ruta_prim = f"/World/{nombre}"
        rep_prim = rep.get.prims(path_pattern=ruta_prim)
        with rep_prim:
            rep.modify.semantics([("class", nombre)])

    # 3. Crear el nuevo contexto o capa de Replicator sobre el stage actual
    with rep.new_layer():
        
        def randomize_hdri():
            hdri_prim = rep.get.prims(path_pattern=dome_light_path)
            with hdri_prim:
                rep.modify.attribute("inputs:texture:file", rep.distribution.choice(HDRI_PATHS))
                rep.modify.pose(rotation=rep.distribution.uniform((0, 0, 0), (0, 360, 0)))
                rep.modify.attribute("inputs:intensity", 1000.0)
                rep.modify.attribute("inputs:exposure", 1.5) 
            return hdri_prim.node
        rep.randomizer.register(randomize_hdri)

        # Crear Iluminación Secundaria (Esferas y Luz Distante)
        distance_light = rep.create.light(rotation=(315, 0, 0), intensity=3000, light_type="distant")

        # Crear Cámara Replicator orientada al origen
        camera = rep.create.camera(position=(25, 25, 25), look_at=(0, 0, 0))
        render_product = rep.create.render_product(camera, (1024, 1024))

        def randomize_sphere_lights():
            lights = rep.create.light(
                light_type="Sphere",
                temperature=rep.distribution.normal(6500, 500),
                intensity=rep.distribution.normal(15000, 5000),
                position=rep.distribution.uniform((-300, -300, -300), (300, 300, 300)),
                scale=rep.distribution.uniform(50, 100),
                count=8
            )
            return lights.node
        rep.randomizer.register(randomize_sphere_lights)

        # 5. Configurar el disparador por cuadro (Trigger)
        with rep.trigger.on_frame(max_execs=2500):
            rep.randomizer.randomize_hdri()
            rep.randomizer.randomize_sphere_lights()
            
            with camera:
                rep.modify.pose(
                    position=rep.distribution.uniform((-4, -4, 1.5), (4, 4, 4)), 
                    look_at=rep.distribution.uniform((-0.05, -0.05, -0.05), (0.05, 0.05, 0.05))
                )

            for nombre in nombres_objetos:
                ruta_prim = f"/World/{nombre}"
                rep_prim = rep.get.prims(path_pattern=ruta_prim)
                with rep_prim:
                    rep.modify.pose(
                        position=rep.distribution.uniform((-0.8, -0.8, 0.0), (0.8, 0.8, 0.5)),
                        rotation=rep.distribution.uniform((0, 0, 0), (10, 360, 10))
                    )

        # 6. Configurar el Escritor de Datos (BasicWriter)
        writer = rep.WriterRegistry.get("BasicWriter")
        writer.initialize(
            output_dir=output_dataset_dir, 
            rgb=True, 
            bounding_box_2d_tight=True
        )
        writer.attach([render_product])

        # 7. Ejecución del Grafo de Replicator
        print("Iniciando la ejecucion del grafo de Replicator...")
        rep.orchestrator.run()
        
        # Esperar hasta que el proceso termine sus iteraciones
        while not rep.orchestrator.get_is_stopped():
            kit_instance.update()

    print(f"Proceso finalizado. Dataset guardado en: {output_dataset_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script Headless para Replicator Randomization en Isaac Sim.")
    parser.add_argument("--usd_path", required=True, help="Ruta del archivo .usd base con materiales aplicados")
    parser.add_argument("--output_dir", required=True, help="Ruta de destino para el dataset final")

    parser.add_argument(
        "--hdri_dir", 
        required=False, 
        default=r"C:\Users\bruni\Documents\HoudiniJOb\hdris", 
        help="Ruta de la carpeta que almacena los HDRIs (Por defecto: C:\\Users\\bruni\\Documents\\HoudiniJOb\\hdris)"
    )
    
    args = parser.parse_args()
    
    print("Inicializando entorno de simulacion...")
    inicializar_omni_headless()
    
    ejecutar_replicator_randomization(args.usd_path, args.hdri_dir, args.output_dir)
    
    if kit_instance:
        kit_instance.close()