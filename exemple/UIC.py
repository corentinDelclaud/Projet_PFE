import sys
import os

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classes.discipline import discipline

poly : discipline
paro : discipline
como : discipline
pedo : discipline
odf : discipline
occl : discipline
ra : discipline
ste : discipline
pano : discipline
cs_urg : discipline
sp : discipline
urg_op : discipline

poly = discipline(1, "Polyclinique", "A101", 20, True, 100)
paro = discipline(2, "Parodontologie", "A102", 15, True, 80)
como = discipline(3, "Comodulation", "A103", 10, True, 60)
pedo = discipline(4, "Pédodontie", "A104", 5, True, 40)
odf = discipline(5, "Orthodontie", "A105", 8, True, 50)
occl = discipline(6, "Occlusodontie", "A106", 12, True, 70)
ra = discipline(7, "Radiologie", "A107", 0, False, 0)
ste = discipline(8, "Stomatologie", "A108", 18, True, 90)
pano = discipline(9, "Panoramique", "A109", 0, False, 0)
cs_urg = discipline(10, "Consultation d'urgence", "A110", 0, False, 0)
sp = discipline(11, "Soins Prothétiques", "A111", 14, True, 85)
urg_op = discipline(12, "Urgences Opératoires", "A112", 0, False, 0)  

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

print("Discipline reels charges avec succes.")
print(poly)
print(paro)
print(como)
print(pedo)
print(odf)
print(occl)
print(ra)
print(ste)
print(pano)
print(cs_urg)
print(sp)
print(urg_op)