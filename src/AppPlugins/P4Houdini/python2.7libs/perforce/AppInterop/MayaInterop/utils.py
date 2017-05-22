def removeStudentTag(fileName):
    try:
        with open(fileName, "r") as f:
            lines = f.readlines()
    except IOError as e:
        print e
        return 1

    try:
        with open(fileName, "w") as f:
            for line in lines:
                if "fileInfo" in line:
                    if "education" in line:
                        print "Removing education flag from file {0}".format(fileName)
                    elif "student" in line:
                        print "Removing student flag from file {0}".format(fileName)
                else:
                    f.write(line)
    except IOError as e:
        print e
        return 1

    return 0