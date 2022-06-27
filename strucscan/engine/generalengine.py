from strucscan.utils import SEPERATOR
from strucscan.scheduler import get_machine_configuration_dict

class GeneralEngine:
    def __init__(self, input_dict):
        """
        Abstract engine object
        :param input_dict: (dict) input dictionary. Please follow to the examples in strucscan.resources.inputyaml
        """
        self.input_dict = input_dict
        self.machinename = self.input_dict["machine"]
        self.machine_configuration_dict = get_machine_configuration_dict(self.machinename)
        self.scheduler = None
        self.name = self.input_dict["engine"].split()[0]
        self.engine_name = "_".join([n for n in self.input_dict["engine"].split()]).replace(".", "_")
        self.properties = self.input_dict["properties"]
        self.prototypes = self.input_dict["prototypes"]
        self.species = self.input_dict["species"]
        self.potential = self.input_dict["potential"]
        self.settings = self.input_dict["settings"]
        self.init_atvolume = self.input_dict["initial atvolume"]

        self.resultfilename = ""

    def set_scheduler(self):
        """
        - assigns strucscan.scheduler.GeneralScheduler object to GeneralEngine

        :return: 0
        """
        try:
            scheduler_name = self.machine_configuration_dict["scheduler"]
            if (scheduler_name.lower() == "sge") or (scheduler_name.lower() == "sungridengine"):
                from strucscan.scheduler import SunGridEngine
                self.scheduler = SunGridEngine(self.machinename)
            elif (scheduler_name.lower() == "slurm"):
                from strucscan.scheduler import Slurm
                self.scheduler = Slurm(self.machinename)
            elif (scheduler_name.lower() == "noqueue"):
                from strucscan.scheduler import NoQueue
                self.scheduler = NoQueue(self.machinename)
        except KeyError:
            raise KeyError("Scheduler name not set in config.yaml.")

    def get_scheduler(self):
        """
        :return: strucscan.scheduler.GeneralScheduler object
        """
        return self.scheduler

    def make_inputfiles(self, machine_info, jobobject):
        """
        - abstract method that creates / writes engine specific input files
        - for VASP, e.g. this method needs to write INCAR, KPOINTS, POSCAR, POTCAR
        - calls strucscan.engine.generalengine.GeneralEngine.get_absolute_jobpath
        - calls strucscan.engine.generalengine.GeneralEngine.make_machinefile
        - calls strucscan.engine.generalengine.GeneralEngine.write_structure

        :param machineconfig: (dict) dictionary of form {"queuename": str, "ncores": int, "nnodes": int}
        :param jobobject: (strucscan.core.jobobject.JobObject object) object that contains information about job
        :return: (str) machine_script_fname
        """
        raise NotImplementedError

    def get_absolute_jobpath(self, property, structpath):
        """
        - abstract method to return absolute path to job directory
        - this is engine specific: 'DATA_TREE_PATH/ENGINE_SIGNATURE/RELATIVE_JOBPATH'
        - while 'DATA_TREE_PATH' is configured in .strucscan and 'RELATIVE_JOBPATH' is generated by
        strucscan.datatree.get_relative_jobpath, 'ENGINE_SIGNATURE' needs to be generated by this method
        - example: 'DATA_TREE_PATH/VASP_5_4_PBE/AlNi/static__L1_2_NiAl'

        :param property: (str) name of property
        :param structpath: (str) absolute path to structure file
        :return: (str) absolute path to job directory
        """
        raise NotImplementedError

    def make_machinefile(self, machineconfig, jobname, ntotalcores, property, nsteps):
        """
        - abstract method to create / write machine script

        :param machineconfig: (dict) machine configuration script taken from 'input_dict'
        :param jobname: (str) name of job, e.g. 'static__fcc__Al'
        :param ntotalcores: (int) number of total cores, that is #cores per node * #of nodes
        :param property: (str) name of property
        :param nsteps: (int) number of single calculation of, e.g. E-V curves, transformation path, ...
        :return: (str list, str) tuple of (list of lines in machine script, machine script file name)
        """
        raise NotImplementedError

    @staticmethod
    def subjobname(species, property):
        """
        :param species: (str) e.g. 'Al Ni'
        :param property: (str) name of property
        :return: (str) job name
        """
        return "".join([s.strip() for s in species]) + SEPERATOR + property

    @staticmethod
    def write_structure(atoms, jobpath, structfilename=None):
        """
        - abstract method to write engine specific structure file

        :param atoms: (ASE atoms object) atoms object with assigned chemical symbols, magnetic moments
        and scaled positions
        :param jobpath: (str) absolute path to job directory
        :param structfilename: (str) name of structure file that is written to disk. for VASP, structfilename is 'POSCAR'
        :return: 0
        """
        raise NotImplementedError

    @staticmethod
    def read_final_structure(path, resultfilename=None):
        """
        - abstract method to read final structure file

        :param path: (str) absolute path to result directory
        :param resultfilename: (str) name of final structure file. for VASP, structfilename is 'OUTCAR.gz'
        :return: (ASE atoms object) final atoms object
        """
        raise NotImplementedError

    def has_resultfile(self, files):
        """
        - VASP specific method to check if the final result file lies in job directory with files

        :param files: (str list) str list of all files in directory
        :return: (bool)
        """
        try:
            for file in files:
                if self.resultfilename in file:
                    return True
            else:
                return False
        except NotADirectoryError:
            raise

    def check_if_finished(self, files):
        """
        - abstract method to check if the calculation in job directory with files with files is finished

        :param files: (str list) str list of all files in directory
        :return: (bool)
        """
        raise NotImplementedError

    def get_result_filename(self):
        """
        - abstract method that returns name of final result file. For VASP, e.g. it is 'OUTCAR'

        :return: (str) name of final result file
        """
        return self.resultfilename

    def submit_job(self, machinefilename):
        """
        - calls strucscan.scheduler.GeneralScheduler.submit

        :param machinefilename: (str) name of machine script file
        :return: (str) id of job. On queuing systems, job_id equilas queue id,
        on systems without queue, job_id euqils process id
        """
        job_id = self.scheduler.submit(machinefilename)
        return job_id

