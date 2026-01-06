import UIC.UIC as uic

poly : uic.UIC
paro : uic.UIC
como : uic.UIC
pedo : uic.UIC
odf : uic.UIC
occl : uic.UIC
ra : uic.UIC
ste : uic.UIC
pano : uic.UIC
cs_urg : uic.UIC
sp : uic.UIC
urg_op : uic.UIC

poly = uic.UIC(1, "Polyclinique", 20, True)
paro = uic.UIC(2, "Parodontologie", 15, True)
como = uic.UIC(3, "Comodulation", 10, True)
pedo = uic.UIC(4, "Pédodontie", 5, True)
odf = uic.UIC(5, "Orthodontie", 8, True)
occl = uic.UIC(6, "Occlusodontie", 12, True)
ra = uic.UIC(7, "Radiologie", 0, False)
ste = uic.UIC(8, "Stomatologie", 18, True)
pano = uic.UIC(9, "Panoramique", 0, False)
cs_urg = uic.UIC(10, "Consultation d'urgence", 0, False)
sp = uic.UIC(11, "Soins Prothétiques", 14, True)
urg_op = uic.UIC(12, "Urgences Opératoires", 0, False)  

poly.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
paro.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, True, True, True, True, True, True, True, True])
como.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
pedo.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, False, False, False, True, True, True, False, True, False])
odf.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, False, True, True, True, False, True, False, True])
occl.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, False, True, False, False, False, True, False, True, False])
ra.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
ste.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
pano.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, False, True, False, True, False, True, False, True])
cs_urg.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
sp.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
urg_op.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, False, False, False, False, False, True, False, True])