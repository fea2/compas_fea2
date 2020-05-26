
try:
    from abaqus import *
    from abaqusConstants import *
except:
    pass

import sys


# Author(s): Andrew Liew (github.com/andrewliew)


if __name__ == "__main__":

    name = sys.argv[-1]
    path = sys.argv[-2]
    cpus = int(sys.argv[-3])
    inp  = '{0}{1}.inp'.format(path, name)
    # user = '{0}{1}.inp'.format('C:/Code/COMPAS/compas_fea2/src/compas_fea2/_core/umat/', 'umat-hooke-iso.f') #TODO change to variables

    if cpus == 1:
        job = mdb.JobFromInputFile(name=name, inputFileName=inp)
    else:
        job = mdb.JobFromInputFile(name=name, inputFileName=inp, numCpus=cpus, numDomains=cpus,
                                   multiprocessingMode=THREADS, parallelizationMethodExplicit=DOMAIN)
                                #    multiprocessingMode=THREADS, parallelizationMethodExplicit=DOMAIN, userSubroutine=user) #TODO change to if statement
    job.submit()
    job.waitForCompletion()
