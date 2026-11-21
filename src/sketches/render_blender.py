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


def surface_finish(mat, kind):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get('Principled BSDF')
    geometry = nodes.new('ShaderNodeNewGeometry')
    noise = nodes.new('ShaderNodeTexNoise')
    links.new(geometry.outputs['Position'], noise.inputs['Vector'])
    noise.inputs['Scale'].default_value = 150 if kind == 'plaster' else 2.8
    noise.inputs['Detail'].default_value = 2
    if kind == 'wood':
        scale = nodes.new('ShaderNodeVectorMath');scale.operation = 'MULTIPLY'
        scale.inputs[1].default_value = (9, 9, .4)
        links.new(geometry.outputs['Position'], scale.inputs[0]);links.new(scale.outputs['Vector'], noise.inputs['Vector'])
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = (.12,.048,.016,1)
        ramp.color_ramp.elements[1].color = (.38,.19,.073,1)
        links.new(noise.outputs['Fac'], ramp.inputs['Fac']);links.new(ramp.outputs['Color'], shader.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .16
    bump.inputs['Distance'].default_value = .008 if kind == 'plaster' else .006
    links.new(noise.outputs['Fac'], bump.inputs['Height']);links.new(bump.outputs['Normal'], shader.inputs['Normal'])


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
    bevel.width = .0015 if spec.get('role')=='wall' else .004 if spec.get('role')=='frame' else .007
    bevel.segments = 2


def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()


def inside_floor(x, y, ring):
    inside = False
    for i, a in enumerate(ring):
        b = ring[i-1]
        if (a['y'] > y) != (b['y'] > y) and x < (b['x']-a['x'])*(y-a['y'])/(b['y']-a['y'])+a['x']:
            inside = not inside
    return inside


def interior_lighting(scene_data, height):
    capture = scene_data.get('camera')
    if not capture or not .1 < capture['position'][1] < height:
        return
    x, _, y = capture['position']
    if not any(inside_floor(x,y,ring) for ring in scene_data['floors']):
        return
    # Soft presentation lights, not electrical fixtures or quoted materials.
    rings = sorted(scene_data['floors'], key=lambda ring: min((p['x']-x)**2+(p['y']-y)**2 for p in ring))[:12]
    for ring in rings:
        cx=sum(p['x'] for p in ring)/len(ring);cy=sum(p['y'] for p in ring)/len(ring)
        if not inside_floor(cx,cy,ring):
            from mathutils.geometry import tessellate_polygon
            triangles=tessellate_polygon([[Vector((p['x'],p['y'],0)) for p in ring]])
            if not triangles:
                continue
            triangle=max(triangles,key=lambda t:(t[1]-t[0]).cross(t[2]-t[0]).length)
            center=sum(triangle,Vector())/3;cx,cy=center.x,center.y
        area=abs(sum(p['x']*ring[(i+1)%len(ring)]['y']-ring[(i+1)%len(ring)]['x']*p['y'] for i,p in enumerate(ring)))/2
        bpy.ops.object.light_add(type='AREA',location=(cx,-cy,min(2.35,height-.15)))
        light=bpy.context.object;light.name='Luz interior de presentación'
        light.data.energy=min(400,max(60,area*12));light.data.color=(1,.95,.87)
        light.data.shape='DISK';light.data.size=max(1,min(2.5,math.sqrt(area)/2))


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
        'window': material('Vidrio', '#e3f1f2', .06),
        'metal': material('Herrajes', '#b8c0c3', .23, .8),
        'sill': material('Repisa', '#dedbd2', .8),
        'roof': material('Cubierta', {'charcoal':'#42494c','terracotta':'#a95338','gray':'#9b9e9f'}[settings.get('roof_color','charcoal')], .5, .25),
        'floor': material('Piso', '#d7d0c0', .75),
    }
    glass = mats['window'].node_tree.nodes.get('Principled BSDF')
    glass.inputs['Transmission Weight'].default_value = .9
    glass.inputs['IOR'].default_value = 1.45
    glass.inputs['Coat Weight'].default_value = .25
    surface_finish(mats['wall'], 'plaster')
    surface_finish(mats['door'], 'wood')
    surface_finish(mats['column'], 'plaster')
    mats['floor'].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = .34 if settings.get('floor_finish','tile')=='tile' else .7
    roof_nodes = mats['roof'].node_tree.nodes
    roof_links = mats['roof'].node_tree.links
    roof_coords = roof_nodes.new('ShaderNodeNewGeometry')
    wave = roof_nodes.new('ShaderNodeTexWave')
    wave.bands_direction = 'X' if settings.get('ridge_axis','x')=='x' else 'Y'
    wave.inputs['Scale'].default_value = 8
    roof_links.new(roof_coords.outputs['Position'], wave.inputs['Vector'])
    roof_bump = roof_nodes.new('ShaderNodeBump')
    roof_bump.inputs['Strength'].default_value = .16
    roof_bump.inputs['Distance'].default_value = .008
    roof_links.new(wave.outputs['Fac'], roof_bump.inputs['Height'])
    roof_links.new(roof_bump.outputs['Normal'], roof_nodes.get('Principled BSDF').inputs['Normal'])
    floor = mats['floor']
    nodes = floor.node_tree.nodes
    links = floor.node_tree.links
    coord = nodes.new('ShaderNodeNewGeometry')
    finish = settings.get('floor_finish','tile')
    if finish != 'concrete':
        brick = nodes.new('ShaderNodeTexBrick')
        links.new(coord.outputs['Position'], brick.inputs['Vector'])
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
    for spec in scene_data.get('details', []):
        box(spec, mats[spec['role']])
    for ring in scene_data['floors']:
        slab = mesh('Piso', [(p['x'],-p['y'],-.008) for p in ring], mats['floor'])
        slab.modifiers.new('Base de presentación', 'SOLIDIFY').thickness = .12
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
    ground = material('Terreno de presentación', '#c7c6bb', .95)
    bpy.ops.mesh.primitive_plane_add(size=radius*200, location=(center.x,center.y,-.15))
    bpy.context.object.data.materials.append(ground)
    capture = scene_data.get('camera')
    bpy.ops.object.camera_add(location=point(capture['position']) if capture else center+Vector((1,-1,.55)).normalized()*radius*3.1)
    camera = bpy.context.object
    aim(camera, point(capture['target']) if capture else center)
    camera.data.lens = 45
    if capture:
        camera.data.type = 'PERSP'
        camera.data.sensor_fit = 'VERTICAL'
        camera.data.angle = math.radians(capture['fov'])
    camera.data.clip_start = .025
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
    interior_lighting(scene_data, high.z)
    scene = bpy.context.scene
    scene.world.use_nodes = True
    sky = scene.world.node_tree.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'NISHITA'
    sky.sun_elevation = math.radians(35)
    sky.sun_rotation = math.radians(130)
    sky.sun_disc = False
    scene.world.node_tree.links.new(sky.outputs['Color'], scene.world.node_tree.nodes['Background'].inputs['Color'])
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .25
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    # CPU presentation profile; verified locally before proposing production use.
    scene.cycles.samples = 24
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = .08
    scene.cycles.adaptive_min_samples = 4
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 6
    scene.view_settings.view_transform = 'AgX'
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
