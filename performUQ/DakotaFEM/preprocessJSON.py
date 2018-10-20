import json
import sys
import os
import platform

numRandomVariables = 0
numNormalUncertain = 0
normalUncertainName=[]
normalUncertainMean =[]
normalUncertainStdDev =[]

numDiscreteDesignSetString = 0
discreteDesignSetStringName=[]
discreteDesignSetStringValues =[]

def preProcessDakota(bimName, evtName, samName, edpName, lossName, simName, driverFile, bldgName, numSamples):

    #setting workflow driver name based on platform
    workflowDriver = 'workflow_driver'
    if platform.system() == 'Windows':
        workflowDriver = 'workflow_driver.bat'

    # 
    # parse the data
    #

    global numRandomVariables
    global numNormalUncertain
    global normalUncertainName
    global normalUncertainMean
    global normalUncertainStdDev

    global numDiscreteDesignSetString
    global discreteDesignSetStringName
    global discreteDesignSetStringValues

    #with open('data.txt', 'w') as outfile:  
    #    json.dump(data, outfile)
    #print data["method"]
    parseFileForRV(bimName)
    parseFileForRV(evtName)
    parseFileForRV(samName)
    #parseFileForRV(simName)
    parseFileForRV(edpName)

    #
    # Write the input file: dakota.in 
    #

    # write out the method data
    f = open('{}/dakota.in'.format(bldgName), 'w')

    f.write("environment\n")
    f.write("tabular_data\n")
    f.write("tabular_data_file = \'dakotaTab.out\'\n\n")

    f.write("method\n")
    f.write("sampling,\n")
    if(not numRandomVariables == 0):
        f.write('samples=' '{}'.format(numSamples))
    else:
        f.write('samples=1')

    #f.write("samples=5\n")
    f.write("\nseed=98765,\n")
    f.write("sample_type random\n")
    f.write('\n\n')

    # write out the variable data
    f.write('variables,\n')
    
    if(numRandomVariables == 0):
        f.write('normal_uncertain = 1\n')
        f.write('means = 1.0\n')
        f.write('std_deviations = 1e-3\n')
        f.write("descriptors = 'dummyRV'\n\n")    

        
    if (numNormalUncertain > 0):
        f.write('normal_uncertain = ' '{}'.format(numNormalUncertain))
        f.write('\n')
        f.write('means = ')
        for i in xrange(numNormalUncertain):
            f.write('{}'.format(normalUncertainMean[i]))
            f.write(' ')
        f.write('\n')

        f.write('std_deviations = ')
        for i in xrange(numNormalUncertain):
            f.write('{}'.format(normalUncertainStdDev[i]))
            f.write(' ')
        f.write('\n')

        f.write('descriptors = ')    
        for i in xrange(numNormalUncertain):
            f.write('\'')
            f.write(normalUncertainName[i])
            f.write('\' ')
        f.write('\n')

    if (numDiscreteDesignSetString > 0):
        f.write('discrete_design_set\n')
        f.write('string ' '{}'.format(numDiscreteDesignSetString))
        f.write('\n')
        f.write('descriptors = ')    
        for i in xrange(numDiscreteDesignSetString):
            f.write('\'')
            f.write(discreteDesignSetStringName[i])
            f.write('\' ')

        f.write('\n')

        f.write('elements_per_variable = ')    
        for i in xrange(numDiscreteDesignSetString):
            #f.write('\'')
            numElements = len(discreteDesignSetStringValues[i])
            f.write(' ' '{}'.format(numElements))
            #f.write(length(discreteDesignSetStringValues[i]))
            print discreteDesignSetStringValues[i]
            print numElements
            #f.write('\' ')

        f.write('\n')
        f.write('elements  ')    
        for i in xrange(numDiscreteDesignSetString):
            elements = discreteDesignSetStringValues[i]
            for j in elements:
                f.write('\'' '{}'.format(j))
                f.write('\' ')
            f.write('\n')

    f.write('\n\n')

    # write out the interface data
    f.write('interface,\n')
    f.write('system # asynch evaluation_concurrency = 4\n')
    f.write("analysis_driver = '{}' \n".format(workflowDriver))
    f.write('parameters_file = \'params.in\' \n')
    f.write('results_file = \'results.out\' \n')
    f.write('work_directory directory_tag \n')
    f.write('copy_files = \'templatedir/*\' \n')
    f.write('named \'workdir\' file_save directory_save\n')
    f.write('aprepro \n')
    f.write('\n')

    #
    # write out the responses
    #

    with open(edpName) as data_file:    
        data = json.load(data_file)

    numResponses=data["total_number_edp"]

    f.write('responses, \n')
    f.write('response_functions = ' '{}'.format(numResponses))
    f.write('\n')
    f.write('response_descriptors = ')    
    #for i in xrange(numResponses):
    for i in xrange(1, numResponses+1):
        f.write('\'a')
        f.write('{}'.format(i))
        f.write('\' ')
    f.write('\n')
    f.write('no_gradients\n')
    f.write('no_hessians\n\n')
    f.close()  # you can omit in most cases as the destructor will call it

    #
    # Write the workflow driver
    #

    f = open('{}/{}'.format(bldgName, workflowDriver), 'w')

    # want to dprepro the files with the random variables
    f.write('perl dpreproSimCenter params.in bim.j ' + bimName + '\n')
    f.write('perl dpreproSimCenter params.in sam.j ' + samName + '\n')
    f.write('perl dpreproSimCenter params.in evt.j ' + evtName + '\n')
    f.write('perl dpreproSimCenter params.in edp.j ' + edpName + '\n')

    scriptDir = os.path.dirname(os.path.realpath(__file__))

    with open(driverFile) as fp:
        for line in fp:
            f.write(line)
            print(line)

    f.write('\n')
    f.write(scriptDir + '/extractEDP ' + edpName + ' results.out \n')

    # Run 
    #f.write('rm -f *.com *.done *.dat *.log *.sta *.msg')
    #f.write('echo 1 >> results.out\n')
    f.close()

    return numRandomVariables

def parseFileForRV(fileName):
    global numRandomVariables
    global numNormalUncertain
    global normalUncertainName
    global normalUncertainMean
    global normalUncertainStdDev

    global numDiscreteDesignSetString
    global normalDiscreteDesignSetName
    global normalDiscreteSetValues

    with open(fileName,'r') as data_file:    
        data = json.load(data_file)

        for k in data["RandomVariables"]:
            if (k["distribution"] == "normal"):
                normalUncertainName.append(k["name"])
                normalUncertainMean.append(k["mean"])
                normalUncertainStdDev.append(k["stdDev"])
                numNormalUncertain += 1
                numRandomVariables += 1

            if (k["distribution"] == "discrete_design_set_string"):
                print k
                discreteDesignSetStringName.append(k["name"])
                elements =[];
                for l in k["elements"]:
                    elements.append(l)
                elements.sort()
                discreteDesignSetStringValues.append(elements)
                print elements
                numDiscreteDesignSetString += 1
                numRandomVariables += 1


    

    