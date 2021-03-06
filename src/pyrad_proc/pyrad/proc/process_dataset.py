"""
pyrad.proc.process_dataset
==========================

Functions for processing Pyrad datasets

    get_process_type
    process_raw
    process_snr
    process_l
    process_cdr
    process_correct_noise_rhohv
    process_echo_id
    process_echo_filter
    process_attenuation
    process_rainrate
    process_hydroclass

"""

from copy import deepcopy

import numpy as np

import pyart

from ..io.read_data import get_datatypefields, get_fieldname_rainbow


def get_process_type(dataset_type):
    """
    maps the dataset type into its processing function and data set format

    Parameters
    ----------
    dataset_type : str
        data set type, i.e. 'RAW', 'SAN', etc.

    Returns
    -------
    func_name : str
        pyrad function used to process the data set type

    dsformat : str
        data set format, i.e.: 'VOL', etc.

    """

    dsformat = 'VOL'
    if dataset_type == 'RAW':
        func_name = 'process_raw'
    elif dataset_type == 'SNR':
        func_name = 'process_snr'
    elif dataset_type == 'RHOHV_CORRECTION':
        func_name = 'process_correct_noise_rhohv'
    elif dataset_type == 'L':
        func_name = 'process_l'
    elif dataset_type == 'CDR':
        func_name = 'process_cdr'
    elif dataset_type == 'SAN':
        func_name = 'process_echo_id'
    elif dataset_type == 'ECHO_FILTER':
        func_name = 'process_echo_filter'
    elif dataset_type == 'ATTENUATION':
        func_name = 'process_attenuation'
    elif dataset_type == 'RAINRATE':
        func_name = 'process_rainrate'
    elif dataset_type == 'HYDROCLASS':
        func_name = 'process_hydroclass'
    else:
        print('ERROR: Unknown dataset type')

    return func_name, dsformat


def process_raw(procstatus, dscfg, radar=None):
    """
    dummy function that returns the initial input data set

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration

    radar : Radar
        Optional. Radar object

    Returns
    -------
    new_dataset : Radar
        radar object

    """

    if procstatus != 1:
        return None

    new_dataset = deepcopy(radar)
    return new_dataset


def process_snr(procstatus, dscfg, radar=None):
    """
    Computes SNR

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration

    radar : Radar
        Optional. Radar object

    Returns
    -------
    new_dataset : Radar
        radar object

    """

    if procstatus != 1:
        return None

    for datatypedescr in dscfg['datatype']:
        datagroup, datatype, dataset, product = get_datatypefields(
            datatypedescr)
        if datatype == 'dBZ':
            refl = 'reflectivity'
        if datatype == 'dBuZ':
            refl = 'unfiltered_reflectivity'
        if datatype == 'dBZv':
            refl = 'reflectivity_vv'
        if datatype == 'dBuZv':
            refl = 'unfiltered_reflectivity_vv'
        if datatype == 'Nh':
            noise = 'noisedBZ_hh'
        if datatype == 'Nv':
            noise = 'noisedBZ_vv'

    if 'output_type' in dscfg:
        if dscfg['output_type'] == 'SNRh':
            snr_field = 'signal_to_noise_ratio_hh'
        elif dscfg['output_type'] == 'SNRv':
            snr_field = 'signal_to_noise_ratio_vv'
    else:
        snr_field = 'signal_to_noise_ratio_hh'

    snr = pyart.retrieve.compute_snr(
        radar, refl_field=refl, noise_field=noise,
        snr_field=snr_field)

    # prepare for exit
    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()
    new_dataset.add_field(snr_field, snr)

    return new_dataset


def process_l(procstatus, dscfg, radar=None):
    """
    Computes L parameter

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration

    radar : Radar
        Optional. Radar object

    Returns
    -------
    new_dataset : Radar
        radar object

    """

    if procstatus != 1:
        return None

    datagroup, datatype, dataset, product = get_datatypefields(
        dscfg['datatype'])
    rhohv = get_fieldname_rainbow(datatype)

    l = pyart.retrieve.compute_l(
        radar, rhohv_field=rhohv,
        l_field='logarithmic_cross_correlation_ratio')

    # prepare for exit
    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()
    new_dataset.add_field('logarithmic_cross_correlation_ratio', l)

    return new_dataset


def process_cdr(procstatus, dscfg, radar=None):
    """
    Computes Circular Depolarization Ratio

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration

    radar : Radar
        Optional. Radar object

    Returns
    -------
    new_dataset : Radar
        radar object

    """

    if procstatus != 1:
        return None

    for datatypedescr in dscfg['datatype']:
        datagroup, datatype, dataset, product = get_datatypefields(
            datatypedescr)
        if datatype == 'RhoHV':
            rhohv = 'cross_correlation_ratio'
        if datatype == 'uRhoHV':
            rhohv = 'uncorrected_cross_correlation_ratio'
        if datatype == 'RhoHVu':
            rhohv = 'unfiltered_cross_correlation_ratio'
        if datatype == 'ZDR':
            zdr = 'differential_reflectivity'

    cdr = pyart.retrieve.compute_cdr(
        radar, rhohv_field=rhohv, zdr_field=zdr,
        cdr_field='circular_depolarization_ratio')

    # prepare for exit
    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()
    new_dataset.add_field('circular_depolarization_ratio', cdr)

    return new_dataset


def process_correct_noise_rhohv(procstatus, dscfg, radar=None):
    """
    identifies echoes as 0: No data, 1: Noise, 2: Clutter,
    3: Precipitation

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration

    radar : Radar
        Optional. Radar object

    Returns
    -------
    new_dataset : Radar
        radar object

    """

    if procstatus != 1:
        return None

    for datatypedescr in dscfg['datatype']:
        datagroup, datatype, dataset, product = get_datatypefields(
            datatypedescr)
        if datatype == 'uRhoHV':
            urhohv = 'uncorrected_cross_correlation_ratio'
        if datatype == 'SNRh':
            snr = 'signal_to_noise_ratio_hh'
        if datatype == 'ZDR':
            zdr = 'differential_reflectivity'
        if datatype == 'Nh':
            nh = 'noisedBZ_hh'
        if datatype == 'Nv':
            nv = 'noisedBZ_vv'

    rhohv = pyart.correct.correct_noise_rhohv(
        radar, urhohv_field=urhohv, snr_field=snr, zdr_field=zdr,
        nh_field=nh, nv_field=nv, rhohv_field='cross_correlation_ratio')

    # prepare for exit
    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()
    new_dataset.add_field('cross_correlation_ratio', rhohv)

    return new_dataset


def process_echo_id(procstatus, dscfg, radar=None):
    """
    identifies echoes as 0: No data, 1: Noise, 2: Clutter,
    3: Precipitation

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration

    radar : Radar
        Optional. Radar object

    Returns
    -------
    new_dataset : Radar
        radar object

    """

    if procstatus != 1:
        return None

    id = np.zeros((radar.nrays, radar.ngates), dtype='int32')+3

    # look for clutter
    gate_filter = pyart.filters.moment_and_texture_based_gate_filter(
        radar, zdr_field=None, rhv_field=None, phi_field=None,
        refl_field=None, textzdr_field=None, textrhv_field=None,
        textphi_field=None, textrefl_field=None, wind_size=7,
        max_textphi=20., max_textrhv=0.3, max_textzdr=2.85,
        max_textrefl=8., min_rhv=0.6)

    is_clutter = gate_filter._gate_excluded is True

    id[is_clutter.nonzero()] = 2

    # look for noise
    is_noise = radar.fields['reflectivity']['data'].data == (
        pyart.config.get_fillvalue())

    id[is_noise.nonzero()] = 1

    id_field = pyart.config.get_metadata('radar_echo_id')
    id_field['data'] = id

    # prepare for exit
    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()
    new_dataset.add_field('radar_echo_id', id_field)

    return new_dataset


def process_echo_filter(procstatus, dscfg, radar=None):
    """
    filters out undesired echo types.
    TODO: make the selection of the echo types to filter and to keep user
    defined

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration

    radar : Radar
        Optional. Radar object

    Returns
    -------
    new_dataset : Radar
        radar object

    """

    if procstatus != 1:
        return None

    is_not_precip = radar.fields['radar_echo_id']['data'] != 3

    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()

    for datatypedescr in dscfg['datatype']:
        datagroup, datatype, dataset, product = get_datatypefields(
            datatypedescr)
        field_name = get_fieldname_rainbow(datatype)
        radar_field = radar.fields[field_name]
        radar_field['data'].data[is_not_precip.nonzero()] = (
            pyart.config.get_fillvalue())
        radar_field['data'].mask[is_not_precip.nonzero()] = True
        new_dataset.add_field('corrected_'+field_name, radar_field)

    return new_dataset


def process_attenuation(procstatus, dscfg, radar=None):
    """
    Computes specific attenuation and specific differential attenuation using
    the Z-Phi method and corrects reflectivity and differential reflectivity

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration

    radar : Radar
        Optional. Radar object

    Returns
    -------
    radar : Radar
        radar object

    """

    if procstatus != 1:
        return None

    for datatypedescr in dscfg['datatype']:
        datagroup, datatype, dataset, product = get_datatypefields(
            datatypedescr)
        if datatype == 'dBZc':
            refl = 'corrected_reflectivity'
        if datatype == 'PhiDPc':
            phidp = 'corrected_differential_phase'
        if datatype == 'ZDRc':
            zdr = 'corrected_differential_reflectivity'
        if datatype == 'dBZ':
            refl = 'reflectivity'
        if datatype == 'PhiDP':
            phidp = 'differential_phase'
        if datatype == 'ZDR':
            zdr = 'differential_reflectivity'

    spec_at, cor_z, spec_diff_at, cor_zdr = (
        pyart.correct.calculate_attenuation(
            radar, doc=15, fzl=None, smooth_window_len=0, a_coef=None,
            beta=None, refl_field=refl, phidp_field=phidp, zdr_field=zdr,
            temp_field=None, spec_at_field=None, corr_refl_field=None,
            spec_diff_at_field=None, corr_zdr_field=None))

    # prepare for exit
    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()

    new_dataset.add_field('specific_attenuation', spec_at)
    new_dataset.add_field('corrected_reflectivity', cor_z)

    if (spec_diff_at is not None) and (cor_zdr is not None):
        new_dataset.add_field(
            'specific_differential_attenuation', spec_diff_at)
        new_dataset.add_field('corrected_differential_reflectivity', cor_zdr)
    else:
        print(
            'WARNING: Specific differential attenuation and \
            attenuation corrected differential reflectivity non available')

    return new_dataset


def process_rainrate(procstatus, dscfg, radar=None):
    """
    Estimates rainfall rate from polarimetric moments

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration

    radar : Radar
        Optional. Radar object

    Returns
    -------
    radar : Radar
        radar object

    """
    if procstatus != 1:
        return None

    if dscfg['RR_METHOD'] == 'Z':
        datagroup, datatype, dataset, product = get_datatypefields(
            dscfg['datatype'][0])
        refl_field = get_fieldname_rainbow(datatype)
        rain = pyart.retrieve.rr_z(
            radar, alpha=0.0376, beta=0.6112, refl_field=refl_field,
            rr_field=None)

    elif dscfg['RR_METHOD'] == 'ZPoly':
        datagroup, datatype, dataset, product = get_datatypefields(
            dscfg['datatype'][0])
        refl_field = get_fieldname_rainbow(datatype)
        rain = pyart.retrieve.rr_zpoly(
            radar, refl_field=refl_field, rr_field=None)

    elif dscfg['RR_METHOD'] == 'KDP':
        datagroup, datatype, dataset, product = get_datatypefields(
            dscfg['datatype'][0])
        kdp_field = get_fieldname_rainbow(datatype)
        rain = pyart.retrieve.rr_kdp(
            radar, alpha=None, beta=None, kdp_field=kdp_field, rr_field=None)

    elif dscfg['RR_METHOD'] == 'A':
        datagroup, datatype, dataset, product = get_datatypefields(
            dscfg['datatype'][0])
        a_field = get_fieldname_rainbow(datatype)
        rain = pyart.retrieve.rr_a(
            radar, alpha=None, beta=None, a_field=a_field, rr_field=None)

    elif dscfg['RR_METHOD'] == 'ZKDP':
        for datatypedescr in dscfg['datatype']:
            datagroup, datatype, dataset, product = get_datatypefields(
                datatypedescr)
            if datatype == 'dBZc':
                refl_field = 'corrected_reflectivity'
            if datatype == 'KDPc':
                kdp_field = 'corrected_specific_differential_phase'
            if datatype == 'dBZ':
                refl_field = 'reflectivity'
            if datatype == 'KDP':
                kdp_field = 'specific_differential_phase'

        rain = pyart.retrieve.rr_zkdp(
            radar, alphaz=0.0376, betaz=0.6112, alphakdp=None, betakdp=None,
            refl_field=refl_field, kdp_field=kdp_field, rr_field=None,
            master_field=refl_field, thresh=10., thresh_max=True)

    elif dscfg['RR_METHOD'] == 'ZA':
        for datatypedescr in dscfg['datatype']:
            datagroup, datatype, dataset, product = get_datatypefields(
                datatypedescr)
            if datatype == 'dBZc':
                refl_field = 'corrected_reflectivity'
            if datatype == 'Ahc':
                a_field = 'corrected_specific_attenuation'
            if datatype == 'dBZ':
                refl_field = 'reflectivity'
            if datatype == 'Ah':
                a_field = 'specific_attenuation'

        rain = pyart.retrieve.rr_za(
            radar, alphaz=0.0376, betaz=0.6112, alphaa=None, betaa=None,
            refl_field=refl_field, a_field=a_field, rr_field=None,
            master_field=refl_field, thresh=0.04, thresh_max=False)

    elif dscfg['RR_METHOD'] == 'hydro':
        for datatypedescr in dscfg['datatype']:
            datagroup, datatype, dataset, product = get_datatypefields(
                datatypedescr)
            if datatype == 'dBZc':
                refl_field = 'corrected_reflectivity'
            if datatype == 'Ahc':
                a_field = 'corrected_specific_attenuation'
            if datatype == 'hydro':
                hydro_field = 'radar_echo_classification'
            if datatype == 'dBZ':
                refl_field = 'reflectivity'
            if datatype == 'Ah':
                a_field = 'specific_attenuation'

        rain = pyart.retrieve.rr_hydro(
            radar, alphazr=0.0376, betazr=0.6112, alphazs=0.1, betazs=0.5,
            alphaa=None, betaa=None, mp_factor=0.6, refl_field=refl_field,
            a_field=a_field, hydro_field=hydro_field, rr_field=None,
            master_field=refl_field, thresh=0.04, thresh_max=False)

    # prepare for exit
    new_dataset = deepcopy(radar)
    new_dataset.fields = dict()
    new_dataset.add_field('radar_estimated_rain_rate', rain)

    return new_dataset


def process_hydroclass(procstatus, dscfg, radar=None):
    """
    Classifies precipitation echoes

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing

    dscfg : dictionary of dictionaries
        data set configuration

    radar : Radar
        Optional. Radar object

    Returns
    -------
    radar : Radar
        radar object

    """
    if procstatus != 1:
        return None

    if dscfg['HYDRO_METHOD'] == 'SEMISUPERVISED':
        for datatypedescr in dscfg['datatype']:
            datagroup, datatype, dataset, product = get_datatypefields(
                datatypedescr)
            if datatype == 'dBZc':
                refl_field = 'corrected_reflectivity'
            if datatype == 'ZDRc':
                zdr_field = 'corrected_differential_reflectivity'
            if datatype == 'RhoHVc':
                rhv_field = 'corrected_cross_correlation_ratio'
            if datatype == 'KDPc':
                kdp_field = 'corrected_specific_differential_phase'
            if datatype == 'TEMP':
                temp_field = 'temperature'
            if datatype == 'dBZ':
                refl_field = 'reflectivity'
            if datatype == 'ZDR':
                zdr_field = 'differential_reflectivity'
            if datatype == 'RhoHV':
                rhv_field = 'cross_correlation_ratio'
            if datatype == 'KDP':
                kdp_field = 'specific_differential_phase'

        mass_centers = np.zeros((9, 5))
        if dscfg['RADARCENTROIDS'] == 'A':
            #      Zh      ZDR     kdp   RhoHV   delta_Z
            mass_centers[0, :] = [
                13.5829,  0.4063, 0.0497, 0.9868,  1330.3]  # DS
            mass_centers[1, :] = [
                02.8453,  0.2457, 0.0000, 0.9798,  0653.8]  # CR
            mass_centers[2, :] = [
                07.6597,  0.2180, 0.0019, 0.9799, -1426.5]  # LR
            mass_centers[3, :] = [
                31.6815,  0.3926, 0.0828, 0.9978,  0535.3]  # GR
            mass_centers[4, :] = [
                39.4703,  1.0734, 0.4919, 0.9876, -1036.3]  # RN
            mass_centers[5, :] = [
                04.8267, -0.5690, 0.0000, 0.9691,  0869.8]  # VI
            mass_centers[6, :] = [
                30.8613,  0.9819, 0.1998, 0.9845, -0066.1]  # WS
            mass_centers[7, :] = [
                52.3969,  2.1094, 2.4675, 0.9730, -1550.2]  # MH
            mass_centers[8, :] = [
                50.6186, -0.0649, 0.0946, 0.9904,  1179.9]  # IH/HDG
        elif dscfg['RADARCENTROIDS'] == 'L':
            #       Zh      ZDR     kdp   RhoHV   delta_Z
            mass_centers[0, :] = [
                13.8231,  0.2514, 0.0644, 0.9861,  1380.6]  # DS
            mass_centers[1, :] = [
                03.0239,  0.1971, 0.0000, 0.9661,  1464.1]  # CR
            mass_centers[2, :] = [
                04.9447,  0.1142, 0.0000, 0.9787, -0974.7]  # LR
            mass_centers[3, :] = [
                34.2450,  0.5540, 0.1459, 0.9937,  0945.3]  # GR
            mass_centers[4, :] = [
                40.9432,  1.0110, 0.5141, 0.9928, -0993.5]  # RN
            mass_centers[5, :] = [
                03.5202, -0.3498, 0.0000, 0.9746,  0843.2]  # VI
            mass_centers[6, :] = [
                32.5287,  0.9751, 0.2640, 0.9804, -0055.5]  # WS
            mass_centers[7, :] = [
                52.6547,  2.7054, 2.5101, 0.9765, -1114.6]  # MH
            mass_centers[8, :] = [
                46.4998,  0.1978, 0.6431, 0.9845,  1010.1]  # IH/HDG
        elif dscfg['RADARCENTROIDS'] == 'P':
            #       Zh      ZDR     kdp   RhoHV   delta_Z
            mass_centers[0, :] = [
                13.9882,  0.2470, 0.0690, 0.9939,  1418.1]  # DS
            mass_centers[1, :] = [
                00.9834,  0.4830, 0.0043, 0.9834,  0950.6]  # CR
            mass_centers[2, :] = [
                05.3962,  0.2689, 0.0000, 0.9831, -0479.5]  # LR
            mass_centers[3, :] = [
                35.3411,  0.1502, 0.0940, 0.9974,  0920.9]  # GR
            mass_centers[4, :] = [
                35.0114,  0.9681, 0.1106, 0.9785, -0374.0]  # RN
            mass_centers[5, :] = [
                02.5897, -0.3879, 0.0282, 0.9876,  0985.5]  # VI
            mass_centers[6, :] = [
                32.2914,  0.7789, 0.1443, 0.9075, -0153.5]  # WS
            mass_centers[7, :] = [
                53.2413,  1.8723, 0.3857, 0.9454, -0470.8]  # MH
            mass_centers[8, :] = [
                44.7896,  0.0015, 0.1349, 0.9968,  1116.7]  # IH/HDG
        elif dscfg['RADARCENTROIDS'] == 'DX50':
            #       Zh      ZDR     kdp   RhoHV   delta_Z
            mass_centers[0, :] = [
                19.0770,  0.4139, 0.0099, 0.9841,  1061.7]  # DS
            mass_centers[1, :] = [
                03.9877,  0.5040, 0.0000, 0.9642,  0856.6]  # CR
            mass_centers[2, :] = [
                20.7982,  0.3177, 0.0004, 0.9858, -1375.1]  # LR
            mass_centers[3, :] = [
                34.7124, -0.3748, 0.0988, 0.9828,  1224.2]  # GR
            mass_centers[4, :] = [
                33.0134,  0.6614, 0.0819, 0.9802, -1169.8]  # RN
            mass_centers[5, :] = [
                08.2610, -0.4681, 0.0000, 0.9722,  1100.7]  # VI
            mass_centers[6, :] = [
                35.1801,  1.2830, 0.1322, 0.9162, -0159.8]  # WS
            mass_centers[7, :] = [
                52.4539,  2.3714, 1.1120, 0.9382, -1618.5]  # MH
            mass_centers[8, :] = [
                44.2216, -0.3419, 0.0687, 0.9683,  1272.7]  # IH/HDG
        else:
            print(
                'WARNING: Unknown radar. \
                Default centroids will be used in classification.')
            mass_centers = None

        hydro = pyart.retrieve.hydroclass_semisupervised(
            radar, mass_centers=mass_centers,
            weights=np.array([1., 1., 1., 0.75, 0.5]), refl_field=refl_field,
            zdr_field=zdr_field, rhv_field=rhv_field, kdp_field=kdp_field,
            temp_field=temp_field, hydro_field=None)

        # prepare for exit
        new_dataset = deepcopy(radar)
        new_dataset.fields = dict()
        new_dataset.add_field('radar_echo_classification', hydro)

        return new_dataset
