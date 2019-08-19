"""
ISIS implementation of reduction path manager
"""
from QueueProcessors.AutoreductionProcessor.paths.reduction_path_manager import ReductionPathManager
from QueueProcessors.AutoreductionProcessor.settings import MISC
import QueueProcessors.AutoreductionProcessor.paths.path_manipulation as paths


class ISISReductionPathManager(ReductionPathManager):
    """
    ISIS version of ReductionPathManager which applies any ISSI specific changes to the data
    paths as well as ensuring the data paths point to the data archive and CEPH
    """

    def __init__(self, input_data_path, instrument, proposal, run_number):
        """
        Use templates from the settings file to populate reduction paths
        :param input_data_path: path to data file
        :param instrument: instrument for reduction
        :param proposal: RB number that relates to the data file
        :param run_number: The run number for the input file
        """
        reduction_script_path = paths.add_to_path(MISC['scripts_directory'] % instrument,
                                                  ['reduce.py'])
        reduction_script_vars_path = paths.add_to_path(MISC['scripts_directory'] % instrument,
                                                       ['reduce_vars.py'])
        temp_output_dir = MISC['temp_root_directory']
        output_directory = MISC['ceph_directory'] % (instrument, proposal, run_number)

        # Excitations would like to remove the run number folder at the end
        if instrument in MISC['excitation_instruments']:
            output_directory = output_directory[:output_directory.rfind('/') + 1]

        ReductionPathManager.__init__(self,
                                      input_data_path=input_data_path,
                                      reduction_script_path=reduction_script_path,
                                      reduction_script_variables_path=reduction_script_vars_path,
                                      temporary_output_directory=temp_output_dir,
                                      final_output_directory=output_directory)
