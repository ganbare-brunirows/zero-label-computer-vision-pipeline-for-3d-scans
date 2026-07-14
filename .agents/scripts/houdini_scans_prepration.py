import os
import sys
import hou

def run_pipeline(target_folder):
    # 1. Initialize a clean, headless Houdini session
    hou.hipFile.clear(suppress_save_prompt=True)

    if not os.path.exists(target_folder):
        print(f"Error: Path '{target_folder}' does not exist.")
        return

    # Get standard context networks
    obj_context = hou.node('/obj')
    stage_context = obj_context.createNode('lopnet', 'stage')

    # Create a geometry network in SOPs for the assets
    geo_net = obj_context.createNode('geo', 'asset_processor')

    # Create a 1m reference Box for the match size node
    box_ref = geo_net.createNode('box', 'ref_1m_cube')
    box_ref.parm('sizex').set(1)
    box_ref.parm('sizey').set(1)
    box_ref.parm('sizez').set(1)
    box_ref.parm('ty').set(0.5)

    sop_nulls = []
    subfolder_names = []

    # Iterate through subfolders
    for idx, subfolder in enumerate(sorted(os.listdir(target_folder))):
        subfolder_path = os.path.join(target_folder, subfolder)
        if not os.path.isdir(subfolder_path):
            continue
        
        obj_file = None
        tex_file = None
        for file in os.listdir(subfolder_path):
            if file.lower().endswith('.obj'):
                obj_file = os.path.join(subfolder_path, file)
            elif file.lower().endswith(('.png', '.jpg', '.jpeg')):
                tex_file = os.path.join(subfolder_path, file)
                
        if not obj_file:
            print(f"Warning: No .obj file found in {subfolder}, skipping.")
            continue
            
        subfolder_names.append(subfolder)
        
        # --- SOP Pipeline Execution ---
        file_node = geo_net.createNode('file', f'file_{subfolder}')
        file_node.parm('file').set(obj_file)
        
        qm_node = geo_net.createNode('quickmaterial', f'quickmat_{subfolder}')
        qm_node.setInput(0, file_node)
        if tex_file:
            qm_node.parm('principledshader_basecolor_texture_1').set(tex_file)
            
        match_size = geo_net.createNode('matchsize', f'matchsize_{subfolder}')
        match_size.setInput(0, qm_node)
        match_size.setInput(1, box_ref)
        match_size.parm('doscale').set(1)
        match_size.parm('justify_y').set(1)
        
        name_node = geo_net.createNode('name', f'name_{subfolder}')
        name_node.setInput(0, match_size)
        name_node.parm('name1').set(subfolder)
        
        null_node = geo_net.createNode('null', subfolder)
        null_node.setInput(0, name_node)
        
        sop_nulls.append(null_node)

    if sop_nulls:
        # --- LOP Pipeline Execution ---
        lop_merge = stage_context.createNode('merge', 'merge_assets')
    
        for idx, null_node in enumerate(sop_nulls):
            s_name = subfolder_names[idx]
            sop_import = stage_context.createNode('sopimport', s_name)
            sop_import.parm('soppath').set(null_node.path())
            sop_import.parm('primpath').set(f'/{s_name}')
            
            lop_merge.setInput(idx, sop_import)
            
        lop_merge.setDisplayFlag(True)
            
        graft_stages = stage_context.createNode('graftstages', 'graft_materials')
        graft_stages.setInput(1, lop_merge)
        graft_stages.parm('destpath').set('/')
        graft_stages.parm('primpath').set('/World')
        
        out_layers = stage_context.createNode('null', 'OUT_LAYERS')
        out_layers.setInput(0, graft_stages)
        
        # 2. SAVE AT TARGET DIRECTORY
        output_usd_path = os.path.join(target_folder, "Geos.usd")
        
        usd_rop = stage_context.createNode('usd_rop', 'usd_export')
        usd_rop.setInput(0, out_layers)
        usd_rop.parm('lopoutput').set(output_usd_path.replace("\\", "/"))
        
        geo_net.layoutChildren()
        stage_context.layoutChildren()
        
        print("Nodes generated successfully in the headless session context!")
        print(f"Cooking layers and rendering USD output to: {output_usd_path}")
        usd_rop.parm('execute').pressButton()
        print("USD Export Complete.")
    else:
        print("No valid geometry targets processed.")

if __name__ == "__main__":
    # Ensure a target path argument was supplied
    if len(sys.argv) < 2:
        print("Usage error: hython build_usd_pipeline.py <path_to_target_folder>")
        sys.exit(1)
        
    # Read the argument directly into the pipeline function
    user_target = sys.argv[1]
    run_pipeline(user_target)