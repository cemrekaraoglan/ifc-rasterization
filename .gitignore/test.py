import ifcopenshell.util.pset


ifc_file = ifcopenshell.open(r"IFC Files\Duplex.ifc")
elements = ifc_file.by_type("IfcBuildingElement")
for element in elements:
    if "concrete" in element.ObjectType.lower():
        print(element.Name)
    
    #print(pset_qto.get_applicable_names("IfcMaterial"))