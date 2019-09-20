from __future__ import print_function
import sys
from matplotlib.backends.backend_pdf import PdfPages
import os
import webbrowser
import subprocess


def export(analysis_pdf_path, module_num, run_num, test_type, fig_list, filename):
    ''' Creates PDF file of all the figures displayed in the notebook
    '''
    # Protecting path from trailing '/' from $HOME
    home_location = os.environ['HOME']
    if home_location[-1] == '/':
        home_location = home_location[:-1]

    #save_path = "{}/develop/projects/lpd/tile_analysis".format(os.environ['HOME'])
    # split() - remove file extension from filename of data
    pdf_name = '{}.pdf'.format(str(module_num)+"_"+str(run_num).zfill(5)+"_"+test_type)
    pdf_file = PdfPages('{}/{}'.format(analysis_pdf_path, pdf_name))
    #open(save_path + "/" + pdf_name) nothing happens 
    
    for figure in fig_list:
        # Insert each figure into PDF created by Matplotlib
        figure.savefig(pdf_file, format='pdf')

    # Add metadata to PDF file
    d = pdf_file.infodict()
    d['Title'] = "Analysis of {}".format(filename)

    pdf_file.close()

    subprocess.Popen(["/usr/bin/evince", analysis_pdf_path + "/" + pdf_name])
    
    return pdf_name
