"""Experiment Configuration"""
import os
import re
import glob
import itertools

import sacred
from sacred import Experiment
from sacred.observers import FileStorageObserver
from sacred.utils import apply_backspaces_and_linefeeds

sacred.SETTINGS['CONFIG']['READ_ONLY_CONFIG'] = False
sacred.SETTINGS.CAPTURE_MODE = 'no'

ex = Experiment('P-Node', save_git_info=False)
ex.captured_out_filter = apply_backspaces_and_linefeeds

source_folders = ['.', './dataloaders_medical', './models', './util']
sources_to_save = list(itertools.chain.from_iterable(
    [glob.glob(f'{folder}/*.py') for folder in source_folders]))
for source_file in sources_to_save:
    ex.add_source_file(source_file)

@ex.config
def cfg():
    """Default configurations"""
    size=256
    input_size = (size, size)
    seed = 1234
    cuda_visable = '0, 1, 2, 3, 4, 5, 6, 7'
    gpu_id = 0
    n_shot = 1
    mode = 'train' # 'train' or 'test'
    # mode = 'test'
    target = 6
    s_idx=0
    add_target=False
    record=False
    # dataset = 'BCV'  # 'VOC' or 'COCO'
    dataset = 'BCV'  # 'VOC' or 'COCO'
    board = "try"

    model_name = "bcv_tar6"
    external_test = "None"  # "decathlon" # "CT_ORG"
    if external_test == "None":
        internal_test = True
    else:
        internal_test = False

    ###  Ode configs
    use_ode = True
    ode_layers = 3
    ode_time = 4
    pretrain_ode = False

    ### Attack configs
    # attack = "PGD"
    attack = "FGSM"
    # attack = "None"
    attack_eps = 0.035
    attack_support = False
    attack_query = True
    attack_visualise = False

    ## gaussian training
    no_samples  = 1
    keep_clean = False
    use_pert_prot = False
    use_cluster = True
    gaussian_std = 0.1
    fine_tune_sup_dir= None
    feat_noise_type = "none"
    input_noise_type = "none"
    cluster_weighting = "none"
    cluster_wt_constant = 1
    cluster_prototype = False
    cluster_supp = True

    save_every=False

    if mode == 'train':
        snapshot  = None
        n_steps = 50000 # 30000
        n_iter=n_steps
        label_sets = 0
        batch_size = 5
        lr_milestones = [10000, 20000, 50000]
        # lr_milestones = [10000, 20000, 30000]
        ignore_label = 255
        print_interval = 100 #100
        save_pred_every = 500
        n_work=1

        task = {
            'n_ways': 1,
            'n_shots': n_shot,
            'n_queries': 1,
        }

        optim = {
            'lr': 1e-3,
            'momentum': 0.9,
            'weight_decay': 0.0005,
        }

    elif mode == 'test':
        
        save_sample = False
        save_name = ""

        notrain = False
        # snapshot = '/home/cse/btech/cs1190341/3D_medical_image_FSS/PANet/work_dir/PANet_BCV_align_sets_0_1way_1shot_train/1/snapshots/last.pth'
        # snapshot = "/home/cse/btech/cs1190341/3D_medical_image_FSS/PANet/work_dir/PANet_BCV_align_sets_0_1way_1shot_train/8/snapshots/last.pth"
        snapshot_old = '/home/cse/btech/cs1190341/3D_medical_image_FSS/PANet/work_dir/PANet_CTORG_align_sets_0_1way_1shot_train/1/snapshots/last.pth'
        # snapshot = '/home/prashant/FSS_m/1way/PANet/model_weights_final/bcv_{}shot_tar{}.pth'.format(n_shot, target)
        # snapshot = "/home/prashant/FSS_m/1way/PANet/work_dir/PANet_BCV_1way_1shot_tar6_train_ode/1/snapshots/last.pth" 
        # snapshot = "/home/prashant/FSS_m/1way/PANet/work_dir/PANet_BCV_1way_1shot_tar6_train_ode/25/snapshots/last.pth" #  VGG modified arch
        # snapshot = "//home/prashant/FSS_m/1way/PANet/work_dir/PANet_BCV_1way_1shot_tar6_train_ode/50/snapshots/last.pth" # adversarial with similarity loss
        # snapshot = "/home/prashant/FSS_m/1way/PANet/work_dir/PANet_BCV_1way_1shot_tar6_train_ode/52/snapshots/last.pth" # adversarial with only PANet loss
        # snapshot = "/home/prashant/FSS_m/1way/PANet/model_weights_adversarial/bcv_tar6_ode_simloss_weighted.pth" # with linearly increasing simloss weights
        # snapshot = "/home/prashant/FSS_m/1way/PANet/model_weights_adversarial/bcv_tar6_ode_simloss_weighted_quad.pth" # with quadratically increasing simloss weights
        # snapshot = "/home/prashant/FSS_m/1way/PANet/model_weights_adversarial/bcv_tar6_ode_simloss_weighted2_query_adv.pth"
        snapshot = "/scratch/cse/btech/cs1190341/CL_FSS/3D_medical_image_FSS_0/PNode-FSS/Al_weights/Liver_ODE.pth"
        
        n_runs = 5
        n_iter = 1
        n_steps = 1000
        batch_size = 1
        scribble_dilation = 0
        bbox = False
        scribble = False

        # Set model config from the snapshot string
        model = {}
        for key in ['align',]:
            model[key] = key in snapshot
        model["adversarial_train"] = True

        # Set label_sets from the snapshot string
        label_sets = int(snapshot_old.split('_sets_')[1][0])

        # Set task config from the snapshot string
        task = {
            'n_ways': 1,
            'n_shots': n_shot,
            'n_queries': 1,
        }

    else:
        raise ValueError('Wrong configuration for "mode" !')


    exp_str = "{}_{}way_{}shot_tar{}_{}".format(dataset, task["n_ways"], task["n_shots"], target, mode)
    if use_ode:
        exp_str += "_ode"

    path = {
        'log_dir': './work_dir',
        'init_path': '/home/prashant/FSS_m/1way/PANet/vgg16-397923af.pth',
        'VOC':{'data_dir': '../../data/Pascal/VOCdevkit/VOC2012/',
               'data_split': 'trainaug',},
        'COCO':{'data_dir': '../../data/COCO/',
                'data_split': 'train',},
    }


    data_srcs = {
        "BCV": "/home/prashant/organ_data/BCV/Training_2d_nocrop",
        "CTORG": "/scratch/cse/btech/cs1190341/CL_FSS/CT_ORG/Training_2d_nocrop",
        "Decathlon": "/scratch/cse/btech/cs1190341/CL_FSS/Decathlon/Training_2d_nocrop",
    }
    
    data_src = data_srcs[dataset]



@ex.config_hook
def add_observer(config, command_name, logger):
    """A hook fucntion to add observer"""
    exp_name = f'{ex.path}_{config["exp_str"]}'
    if config['mode'] == 'test':
        if config['notrain']:
            exp_name += '_notrain'
        if config['scribble']:
            exp_name += '_scribble'
        if config['bbox']:
            exp_name += '_bbox'
    observer = FileStorageObserver.create(os.path.join(config['path']['log_dir'], exp_name))
    ex.observers.append(observer)
    return config
