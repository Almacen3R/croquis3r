"""Trusted Blender entry point. Data-only scene from validated render queue JSON.

World contract: browser (x, up, plan-y) -> Blender (x, -plan-y, up).
Run with --factory-startup --disable-autoexec; never load user .blend files.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def point(p):
    return (p[0], -p[2], p[1])


def material(name, color, roughness=.6, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    node = mat.node_tree.nodes.get('Principled BSDF')
    rgb = tuple(int(color[i:i+2], 16)/255 for i in (1, 3, 5))
    rgb = tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb)
    node.inputs['Base Color'].default_value = (*rgb, 1)
    node.inputs['Roughness'].default_value = roughness
    node.inputs['Metallic'].default_value = metallic
    return mat


def mesh(name, points, mat):
    data = bpy.data.meshes.new(name)
    order = list(range(len(points)))
    if sum(p[0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*p[1] for i,p in enumerate(points)) < 0:
        order.reverse()
    data.from_pydata(points, [], [order])
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def box(spec, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=point(spec['position']))
    obj = bpy.context.object
    obj.dimensions = (spec['size'][0], spec['size'][2], spec['size'][1])
    obj.rotation_euler.z = spec['rotation']
    obj.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new('Soft edges', 'BEVEL')
    bevel.width = .007
    bevel.segments = 2


def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    scene_data = json.loads(Path(args[0]).read_text(encoding='utf-8'))
    output = Path(args[1])
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    settings = scene_data.get('settings', {})
    mats = {
        'wall': material('Pintura', {'ivory':'#f5eddb','white':'#ffffff','sand':'#d9bf9d','sage':'#a5b4a1'}[settings.get('wall_color','ivory')], .85),
        'frame': material('Marcos', '#283333', .35, .4),
        'column': material('Columnas', '#bcb7ac', .9),
        'door': material('Puertas', '#8f5830', .65),
        'window': material('Vidrio', '#7da8b4', .16, .25),
        'roof': material('Cubierta', {'charcoal':'#42494c','terracotta':'#a95338','gray':'#9b9e9f'}[settings.get('roof_color','charcoal')], .5, .25),
        'floor': material('Piso', '#d7d0c0', .75),
    }
    glass = mats['window'].node_tree.nodes.get('Principled BSDF')
    glass.inputs['Transmission Weight'].default_value = .5
    floor = mats['floor']
    nodes = floor.node_tree.nodes
    links = floor.node_tree.links
    coord = nodes.new('ShaderNodeTexCoord')
    finish = settings.get('floor_finish','tile')
    if finish != 'concrete':
        brick = nodes.new('ShaderNodeTexBrick')
        links.new(coord.outputs['Position'] if 'Position' in coord.outputs else coord.outputs['Object'], brick.inputs['Vector'])
        brick.inputs['Scale'].default_value = 1
        brick.inputs['Brick Width'].default_value = 1.2 if finish == 'wood' else .6
        brick.inputs['Row Height'].default_value = .2 if finish == 'wood' else .6
        brick.inputs['Mortar Size'].default_value = .003
        brick.inputs['Color1'].default_value = (.42,.22,.09,1) if finish == 'wood' else (.72,.68,.6,1)
        brick.inputs['Color2'].default_value = (.55,.33,.14,1) if finish == 'wood' else (.78,.74,.66,1)
        links.new(brick.outputs['Color'], nodes.get('Principled BSDF').inputs['Base Color'])
    for spec in scene_data['boxes']:
        box(spec, mats[spec['role']])
    for spec in scene_data['openings']:
        box(spec, mats[spec['kind']])
    for ring in scene_data['floors']:
        mesh('Piso', [(p['x'],-p['y'],-.008) for p in ring], mats['floor'])
    for face in scene_data['roof']['surfaces']:
        obj = mesh('Techo', [point(p) for p in face], mats['roof'])
        solid = obj.modifiers.new('Espesor cubierta', 'SOLIDIFY')
        solid.thickness = .08
    for face in scene_data['roof']['closures']:
        mesh('Cierre de cubierta', [point(p) for p in face], mats['wall'])
    # Bounds from house geometry only; ground and studio lights do not alter framing.
    bpy.context.view_layer.update()
    points = [obj.matrix_world @ Vector(corner) for obj in bpy.context.scene.objects if obj.type == 'MESH' for corner in obj.bound_box]
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (low+high)/2
    radius = max(2, (high-low).length/2)
    ground = material('Terreno de presentación', '#b3b9a1', .95)
    bpy.ops.mesh.primitive_plane_add(size=radius*20, location=(center.x,center.y,-.05))
    bpy.context.object.data.materials.append(ground)
    bpy.ops.object.camera_add(location=center+Vector((1,-1,.78)).normalized()*radius*3.1)
    camera = bpy.context.object
    aim(camera, center)
    camera.data.lens = 45
    camera.data.clip_end = 2000
    bpy.context.scene.camera = camera
    bpy.ops.object.light_add(type='SUN', location=(0,0,10))
    sun = bpy.context.object
    sun.rotation_euler = (math.radians(25),math.radians(-25),math.radians(-30))
    sun.data.energy = 2.5
    sun.data.angle = .15
    bpy.ops.object.light_add(type='AREA', location=center+Vector((-radius,-radius,radius*2)))
    area = bpy.context.object
    area.data.energy = 500*radius
    area.data.shape = 'DISK'
    area.data.size = radius*2
    aim(area,center)
    scene = bpy.context.scene
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.65,.75,.9,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .45
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    # A CPU preview must complete on sales workstations without expensive denoiser
    # kernel initialization. Larger offline/publicity profiles can be added later.
    scene.cycles.samples = 16
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = .1
    scene.cycles.adaptive_min_samples = 4
    scene.cycles.use_denoising = False
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(output)
    scene.render.use_file_extension = True
    bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    main()
