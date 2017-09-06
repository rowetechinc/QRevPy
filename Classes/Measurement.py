from Classes.MMT_TRDI import MMT_TRDI
import numpy as np
import os
from Classes.TransectData import TransectData
from Pd0TRDI import Pd0TRDI

class Measurement(object):
    """Class to hold measurement details for use in the GUI
        Analogous to matlab class: clsMeasurement
    """

    def __init__(self, in_file, source='TRDI'):
        self.station_name = None
        self.station_number = None
        self.transects = []
        self.mb_tests = None
        self.sys_test = None
        self.compass_cal = None
        self.compass_eval = None
        self.ext_temp_chk = None
        self.extrap_fit = None
        self.processing = None
        self.comments = None
        self.discharge = None
        self.uncertainty = None
        self.intitial_settings = None
        self.qa = None
        self.userRating = None
        
        if source == 'TRDI':
            self.load_trdi(in_file, **{'type': 'Q', 'checked': False})

    def load_trdi(self, mmt, **kargs):
        '''method to load trdi MMT file'''

        #read in the MMT file
        self.trdi = MMT_TRDI(mmt)
        mmt = self.trdi
    
        #Get properties if they exist, otherwise set them as blank strings
        self.station_name = str(self.trdi.site_info['Name'])
        
        self.station_number = str(self.trdi.site_info['Number'])
        
        self.processing = 'WR2'

#         if len(kargs) > 1:
#             self.transects = TransectData('TRDI', mmt,'Q',kargs[1])
#         else:

        #Refactored from TransectData to iteratively create TransectData objects
        #----------------------------------------------------------------
        if kargs['type'] == 'Q':
            transects = 'transects'
            active_config = 'active_config' 
            
            if kargs['checked'] == True:
                files_to_load = np.array([x.Checked for x in mmt.transects], dtype=bool)
                file_names = [x.Files for x in mmt.transects]
            else:
                files_to_load = np.array(np.ones(len(mmt.transects)), dtype=bool)
                file_names = [x.Files for x in mmt.transects]
                    
                
        elif kargs['type'] == 'MB':
            transects = 'mbt_transects'
            active_config = 'mbt_active_config'
            files_to_load = np.array(mmt.mbt_transects.Checked, dtype=bool)
            file_names = [x.Files for x in mmt.mbt_transects if x.Checked == 1]
        
        files_to_load_idx = np.where(files_to_load == True)[0]
          
        pathname = mmt.infile[:mmt.infile.rfind('/')]
        
        # Determine if any files are missing
        
        valid_files = []
        for x in file_names:
            x[0].Path = x[0].Path[x[0].Path.rfind('\\') + 1:]
            if os.path.exists(''.join([pathname,'/',x[0].Path])):
                valid_files.append((x, 1))
            else:
                valid_files.append((None, 0))
                
        
        pd0_data = [Pd0TRDI(''.join([pathname,'/',x[0][0].Path])) for x in valid_files if x[1] == 1]
        
        # Process each transect
        for k in range(len(pd0_data)):
            
            transect = TransectData()
            transect.active_config = active_config
            transect.transects = transects
                
            transect.get_data('TRDI', mmt.transects[k], pd0_data[k], files_to_load_idx[k])
            self.transects.append(transect)
            
        #-------------------------Done Refactor----------------------------------------------
        
        







