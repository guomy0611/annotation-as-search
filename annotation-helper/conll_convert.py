from pathlib import Path
from sys import exit


def conll06_to_conll09(filename):
    """
    convert connl06-file to a conll09-file

    convert input file to a 'pseudo' conll09-file and save conll09-file as
    {filename}_converted.conll
    arguments:
        filename: name of the input conll06-file if file is 
            in the same folder, path+filename otherwise
    returns:
        None
    """
    # check if file exists
    file = Path("./" + filename)
    if file.is_file():
        output = open(filename[:-6] + "_converted.conll", "w")
        with file.open() as f:
            for line in f:
                line = line.strip()
                # skip blank line and enter line break
                if not line:
                    output.write("\n")
                    continue
                lines = line.split()
                # write conll09-line to output-file, '_' is unknown information, 
		# lines[4] is not part of conll09 
		# ugly but fast!
		new_line = lines[0] + "\t" + lines[1] + "\t" + lines[2] + "\t"
                             + "_" + "\t" + lines[3] + "\t" + "_" + "\t" + lines[5]
                             + "\t" + "_\t" + lines[6] + "\t" + "_\t" + lines[7]
                             + "\t_\t_\t_\t_\n"
                output.write(new_line)
        output.close()

    # file does nox exist -> exit
    else:
        print("File does not exist. Abort")
        exit()


def conll09_to_conll06(filename):
    """
    convert connl09-file to a conll06-file,

    convert input file to a 'pseudo' conll06-file and save conll06-file as
    {filename}_converted_converted_to_06.conll

    arguments:
        filename: name of the input conll09-file if file is 
            in the same folder, path+filename otherwise
    returns:
        None
    """

    #check if file exists
    file = Path("./" + filename)
    if file.is_file():
        output = open(filename[:-6] + "_converted_to_06.conll", "w")

        with file.open() as f:

            for line in f:
                line = line.strip()
                # skip blank line and enter line break
                if not line:
                    output.write("\n")
                    continue
                lines = line.split()
                new_line = "\t".join(lines[:3])
                last = "\t".join(lines[10:13]) + "\n"
                new_line += "\t" + lines[4] + "\t" + lines[4] + "\t" \
                            + lines[6] + "\t" + lines[8] + "\t"
                # write conll09-line to output-file
                output.write(new_line+last)
            output.close()

    # file does nox exist -> exit
    else:
        print("File does not exist. Abort.")
        exit()



if __name__ == '__main__':
    conll06_to_conll09("test.German.gold.conll")
    conll09_to_conll06("test.German.gold_converted.conll")
