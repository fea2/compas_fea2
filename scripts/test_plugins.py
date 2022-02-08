import compas_fea2
from compas_fea2.model import Model
from compas_fea2.model import Material, Steel, Concrete
from compas_fea2.model import Section, BoxSection
from compas_fea2.problem import Problem

compas_fea2.set_backend('abaqus')

model = Model(name='test', description='testing...', author='tom')
material = Material(name='plastic')
steel = Steel(name='S355', fy=355, fu=None, eu=20, E=210, v=0.3, p=7850)
concrete = Concrete(name='C20', fck=20, v=0.2, p=2400, fr=None)
section = Section(name='section', material=steel)
box = BoxSection(name='box', b=0.1, h=0.2, tw=0.005, tf=0.005, material=concrete)

problem = Problem('test2', model, author='tomtom')


print(model)
print(material)
print(steel)
print(concrete)
print(section)
print(box)

print(problem)
