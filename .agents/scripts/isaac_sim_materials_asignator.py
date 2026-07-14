import os
import argparse

def aplicar_semantica_headless(prim_objetivo, nombre_clase):
    from pxr import Sdf, Usd
    prim_objetivo.AddAppliedSchema("SemanticsAPI:class")
    sem_type = prim_objetivo.CreateAttribute("semantic:class:semanticType", Sdf.ValueTypeNames.String, True)
    sem_type.Set("class")
    sem_data = prim_objetivo.CreateAttribute("semantic:class:semanticData", Sdf.ValueTypeNames.String, True)
    sem_data.Set(nombre_clase)
    print(f"   ↳ 🏷 Semántica aplicada: [class: {nombre_clase}]")

def procesar_escenario_headless(usd_input_path, carpeta_texturas):
    from pxr import Sdf, UsdShade, Usd
    
    if not os.path.exists(usd_input_path):
        print(f"Error: El archivo USD no existe en {usd_input_path}")
        return
    if not os.path.exists(carpeta_texturas):
        print(f" Error: La carpeta de texturas no existe en {carpeta_texturas}")
        return

    directorio, nombre_archivo = os.path.split(usd_input_path)
    nombre_base, extension = os.path.splitext(nombre_archivo)
    usd_output_path = os.path.join(directorio, f"{nombre_base}_with_materials{extension}").replace("\\", "/")
    
    print(f"📂 Cargando escenario USD: {usd_input_path}")
    
    stage = Usd.Stage.Open(usd_input_path)
    if not stage:
        print("Error crítico: No se pudo abrir el archivo USD.")
        return

    MATERIAL_SCOPE_PATH = "/World/Looks"
    if not stage.GetPrimAtPath(MATERIAL_SCOPE_PATH):
        stage.DefinePrim(MATERIAL_SCOPE_PATH, "Scope")

    from pxr import UsdLux
    base_light_path = "/World/BaseLight"
    if not stage.GetPrimAtPath(base_light_path):
        base_light = UsdLux.DistantLight.Define(stage, base_light_path)
        base_light.CreateIntensityAttr(0.0)
        print(f"💡 Luz base insertada en {base_light_path} para prevenir Auto-Lighting.")

    for nombre_subcarpeta in os.listdir(carpeta_texturas):
        ruta_subcarpeta = os.path.join(carpeta_texturas, nombre_subcarpeta)
        if os.path.isdir(ruta_subcarpeta):
            ruta_imagen = None
            for archivo in os.listdir(ruta_subcarpeta):
                if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                    ruta_imagen = os.path.join(ruta_subcarpeta, archivo).replace("\\", "/")
                    break 
            
            if not ruta_imagen:
                continue
            
            material_path = f"{MATERIAL_SCOPE_PATH}/{nombre_subcarpeta}"
            shader_node_path = f"{material_path}/Shader"
            
            material_prim = UsdShade.Material.Define(stage, material_path)
            shader_prim = UsdShade.Shader.Define(stage, shader_node_path)
            
            # Use OmniPBR mdl
            shader_prim.CreateIdAttr("OmniPBR")
            shader_prim.SetSourceAsset(Sdf.AssetPath("OmniPBR.mdl"), "mdl")
            shader_prim.SetSourceAssetSubIdentifier("OmniPBR", "mdl")
            
            shader = shader_prim
            specular_input = shader.CreateInput("specular_level", Sdf.ValueTypeNames.Float)
            specular_input.Set(0.0)
            
            enable_diffuse_input = shader.CreateInput("enable_diffuse_texture", Sdf.ValueTypeNames.Bool)
            enable_diffuse_input.Set(True)
            
            texture_input = shader.CreateInput("diffuse_texture", Sdf.ValueTypeNames.Asset)
            texture_input.Set(Sdf.AssetPath(ruta_imagen))
            
            material_output = material_prim.CreateSurfaceOutput("mdl")
            material_output.ConnectToSource(shader_prim.ConnectableAPI(), "out")
            
            print(f"✔ Material generado en USD: {material_path}")
            
            prim_objetivo_path = f"/World/{nombre_subcarpeta}"
            prim_objetivo = stage.GetPrimAtPath(prim_objetivo_path)
            
            if prim_objetivo.IsValid():
                UsdShade.MaterialBindingAPI(prim_objetivo).Bind(material_prim)
                print(f"   ↳ 🔗 Vinculado de manera exitosa al Prim: {prim_objetivo_path}")
                aplicar_semantica_headless(prim_objetivo, nombre_subcarpeta)

    stage.Export(usd_output_path)
    print(f"¡Hecho! El escenario modificado con materiales y semántica se guardó en: {usd_output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesador Headless de Materiales y Semántica para Isaac Sim.")
    parser.add_argument("--usd_path", required=True, help="Ruta absoluta al archivo .usd original")
    parser.add_argument("--textures_path", required=True, help="Ruta de la carpeta raíz que contiene las subcarpetas con texturas")
    args = parser.parse_args()
    procesar_escenario_headless(args.usd_path, args.textures_path)