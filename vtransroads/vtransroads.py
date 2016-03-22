import networkx
import fiona


aotclass_mapping = [
    ([7], 'trail'),
    ([4], 'class4'),
    ([3], 'class3'),
    ([2]+range(21,30), 'class2'),
    ([1]+range(11,20), 'class1'),
    (range(30, 40), 'stateroute'),
    (range(40,50), 'usroute'),
    (range(51, 60), 'interstate'),
    ([5,6], 'forestservice')
]

surface_mapping = [
    ([1], 'paved'), 
    ([2,3,5,6,9], 'notpaved')
]

def expand_mapping(mapping):
    result = {}
    for k, v in mapping:
        for k2 in k:
            result[k2] = v
    return result
    
aotclass_mapping = expand_mapping(aotclass_mapping)
surface_mapping = expand_mapping(surface_mapping)

def drop(props):
    aotclass = props['AOTCLASS']
    if aotclass not in aotclass_mapping:
        return True
    else:
        return False

def get_tags(props):
    aotclass = props['AOTCLASS']
    surface = props['SURFACETYP']
    
    tags = [
        aotclass_mapping[aotclass],
        surface_mapping[surface]
    ]
    
    return tags
    

def drop_z(coords):
    return zip(*zip(*coords)[:2])

def get_rounded_coords(nd_coords):
    x,y = nd_coords
    return int(round(x)), int(round(y))

node_labels = {}
def get_node_label(nd_coords):
    if nd_coords in node_labels:
        return node_labels[nd_coords]
    else:
        if not node_labels:
            label = 0
        else:
            label = max(node_labels.values()) + 1
        node_labels[nd_coords] = label
        return label 

def get_multi_graph(path):        
    
    g = networkx.MultiGraph()
    
    with fiona.open(path) as c:
        
        crs = c.crs
        
        for rec in c:
            
            props = rec['properties']
            
            if drop(props):
                continue
            
            tags = get_tags(props)
            
            geom = rec['geometry']
            assert geom['type'] == 'LineString'
            
            coords = geom['coordinates']
            coords = drop_z(coords)
            
            nda_coords = get_rounded_coords(coords[0])
            ndb_coords = get_rounded_coords(coords[-1])
            
            nda = get_node_label(nda_coords)
            ndb = get_node_label(ndb_coords)
            
            if 'interstate' in tags:
                travel_order = [(nda, ndb)]
            else:
                travel_order = [(nda, ndb), (ndb, nda)]
        
        
            g.add_edge(
                nda, ndb, 
                coords = coords[1:-1],
                shape_order = (nda, ndb),
                travel_order = travel_order,
                tags = tags
            )
            
            g.node[nda]['coords'] = nda_coords
            g.node[ndb]['coords'] = ndb_coords
            
    return g, crs
        
        
if __name__ == "__main__":
    import cPickle
    import sys
    
    in_path, out_path = sys.argv[1:3]
    
    g, crs = get_multi_graph(in_path)
    from vtransweights import weight_presets
    
    with open(out_path,'wb') as f:
        cPickle.dump((g, weight_presets, crs), f)





