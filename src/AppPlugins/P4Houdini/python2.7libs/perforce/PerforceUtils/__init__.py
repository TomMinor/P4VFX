def parsePerforceError(e):
    eMsg = str(e).replace("[P4#run]", "")
    idx = eMsg.find('\t')
    firstPart = " ".join(eMsg[0:idx].split())
    firstPart = firstPart[:-1]
    
    secondPart = eMsg[idx:]
    secondPart = secondPart.replace('\\n', '\n')
    secondPart = secondPart.replace('"', '')
    secondPart = " ".join(secondPart.split())
    secondPart = secondPart.replace(' ', '', 1) # Annoying space at the start, remove it
    
    eMsg = "{0}\n\n{1}".format(firstPart, secondPart)

    type = "info"
    if "[Warning]" in str(e):
        eMsg = eMsg.replace("[Warning]:", "")
        type = "warning"
    elif "[Error]" in str(e):
        eMsg = eMsg.replace("[Error]:", "")
        type = "error"
    
    return eMsg, type

# def loadP4Config(p4):
#     # Stupid bug (Windows only I hope)
#     if p4.p4config_file == "noconfig":
#         configpath = os.environ['P4CONFIG'].replace('\\', '/') 
#         print os.path.isfile( configpath )
#         print os.path.isfile("C:/Users/tom/.p4config")
#         if os.path.isfile( os.environ['P4CONFIG'].replace('\\', '/') ):
#             p4Logger().info("Reading from config file at {0}".format(os.environ['P4CONFIG']) )
#             with open( os.environ['P4CONFIG'] ) as file:
#                 for line in file:
#                     key, value = line.split("=")
#                     p4Logger().info("Setting {0}={1}".format(key,value))
#                     p4.set_env(key, value)

# # ToDo rewrite this AWFUL function
# def writeToP4Config(config, key, value):
#     return

#     found = False
#     fileinput.close()
    
#     p4Logger().info("Writing {0}:{1} to config {2}".format(key, value, config))

#     if config == 'noconfig':
#         raise RuntimeError('No configuration file found (%s)' % config)

#     try:
#         for line in fileinput.input(config, inplace=True):
#             result = line
#             resultSplit = line.split("=")
            
#             if len(resultSplit) == 2:
#                 _key, _value = resultSplit
#                 if _key == key:
#                     result = "{0}={1}\n".format( key, value )
#                     found = True
                    
#             print "\n" + result + "\n",
            
#         if not found:
#             with open(config, "a") as file:
#                 file.write( "{0}={1}\n".format( key, value ) )
#     except Exception as e:
#         p4Logger().error(e)