import omni.replicator.core as rep
import omni.usd
from pxr import UsdGeom
import os

# 1. Configuracion
# Guarda los datos en una nueva carpeta temporal para las pruebas de GUI
output_dataset_dir = r"C:\Users\bruni\Documents\HoudiniJOb\RawCanMeshes\dataset_gui_test"

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

# 2. Obtener el Stage actual (ya debe estar abierto en la GUI)
stage = omni.usd.get_context().get_stage()
world_prim = stage.GetPrimAtPath("/World")

# Crear una luz base temporal de inmediato para desactivar el "Auto-Lighting" de Isaac Sim
from pxr import UsdLux
base_light = UsdLux.DistantLight.Define(stage, "/World/BaseLight")
base_light.CreateIntensityAttr(0.0)

nombres_objetos = []
if world_prim and world_prim.IsValid():
    for child in world_prim.GetChildren():
        if child.GetName() not in ["Looks", "Camera", "HDRI_DomeLight", "BaseLight"] and (child.IsA(UsdGeom.Xform) or child.IsA(UsdGeom.Mesh)):
            nombres_objetos.append(child.GetName())

print(f"Objetos detectados para aleatorizar: {nombres_objetos}")

# 3. Detener orquestador por si estaba corriendo
rep.orchestrator.stop()

# 3.5 Crear el Domo de Iluminación manualmente
from pxr import UsdLux
dome_light_path = "/World/HDRI_DomeLight"
dome_usd = UsdLux.DomeLight.Define(stage, dome_light_path)
dome_usd.CreateIntensityAttr(1000.0)

# 4. Crear la capa de Replicator
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

    # Crear Luz Distante de Relleno
    distance_light = rep.create.light(rotation=(315, 0, 0), intensity=3000, light_type="distant")

    # Crear Cámara
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

    # Trigger de Replicator
    with rep.trigger.on_frame(max_execs=50):
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

    # Configurar Escritura
    writer = rep.WriterRegistry.get("BasicWriter")
    writer.initialize(
        output_dir=output_dataset_dir, 
        rgb=True, 
        bounding_box_2d_tight=True
    )
    writer.attach([render_product])
    
    print("Iniciando Grafo de Replicator...")
    # Correr en la GUI asíncronamente
    rep.orchestrator.run()
