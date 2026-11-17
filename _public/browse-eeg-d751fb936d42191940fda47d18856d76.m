% Raw EEG browsing example for the Neurodesk FieldTrip tutorial.
% Download Data_sample.zip as described in the tutorial before running.
cfg = [];
cfg.dataset = fullfile(getenv('HOME'), 'neurodesktop-storage', 'EEGDemo', ...
    'Data_sample', 'sub-01', 'eeg', 'sub-01_task-FeatAttnDec_eeg.vhdr');
% Use the native BrainVision header and markers. This sample's JSON stores
% SamplingFrequency as text, which FieldTrip 20211114 interprets incorrectly.
cfg.readbids = false;
cfg.continuous = 'yes';
cfg.viewmode = 'vertical';
cfg.blocksize = 10;
cfg.preproc.demean = 'yes';
cfg.ylim = [-100 100];
cfg = ft_databrowser(cfg);
