#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Plot Vertical loss of Ox by family. Function can also print budget to csv.

This is an example script to use AC_tools KPP mechanism parsing/tagging functions. The

python AC_tools/Scripts/analyse_vertical_Ox_loss_by_route_in_KPP_mech.py <working directory with NetCDF of GEOS-Chem output>

"""
import AC_tools as AC
import numpy as np
import sys
import matplotlib.pyplot as plt
import pandas as pd
from netCDF4 import Dataset
import os


def main():
    """
    Driver for analysis of LOx via KPP in GEOS-Chem

    Notes
    -----
     - comment/uncommet functions as required
    """
    # Plot vertical odd oxygen (Ox) loss via route (chemical family)
#    plot_vertical_fam_loss_by_route()
    # Analyse odd oxygen (Ox) loss budget via route (chemical family)
    calc_fam_loss_by_route()


def plot_vertical_fam_loss_by_route(fam='LOx', ref_spec='O3', region=None,
                                    wd=None, Mechanism='Halogens', rm_strat=False,
                                    weight_by_num_molecules=True, verbose=True, debug=False):
    """
    Plot vertical odd oxygen (Ox) loss via route (chemical family)

    Parameters
    -------
    fam (str): tagged family to track (already compiled in KPP mechanism)
    ref_spec (str): reference species to normalise to
    region (str): region to consider (by masking all but this location)
    wd (str): working directory ("wd") of model output
    Mechanism (str): name of the KPP mechanism (and folder) of model output
    weight_by_num_molecules (boolean): weight grid boxes by number of molecules
    rm_strat (boolean): (fractionally) replace values in statosphere with zeros
    debug, verbose (bool): switches to turn on/set verbosity of output to screen

    Returns
    -------
    (None)

    Notes
    -----
     - AC_tools includes equivlent functions for smvgear mechanisms
    """
    # --- Local variables/ Plot extraction / Settings
    # Get dictionaries of shared data and variables for model output
    Var_rc, Data_rc = func_settings(full_vertical_grid=True, wd=wd)
    # assume name and location of code directory
    wd = Var_rc['wd']
    assert os.path.exists(wd), 'working directory not found @: {}'.format(wd)
    CODE_wd = '{}/../code/KPP/{}/'.format(wd, Mechanism)
    assert os.path.exists(CODE_wd), 'code directory not found @: ' + CODE_wd
    # plot up as % contribution to vertical Ox loss?
    plt_normalised_by_vertical = True
    # analyse and save this as a .csv
    analyse_and_print = True
    # Limit altitude (to compare with ACP troposphere only papers )
    limit_plotted_alititude = True
    # --- Get information KPP mechanism (inc. tags for families, rxn. strs)
    # Reaction dictionary
    RR_dict = AC.get_dict_of_KPP_mech(wd=CODE_wd,
                                      GC_version=Data_rc['GC_version'], Mechanism=Mechanism)
    if debug:
        print(len(RR_dict), [RR_dict[i] for i in RR_dict.keys()[:5]])
    # Get tags for family
    tags_dict = AC.get_tags4_family(fam=fam, wd=CODE_wd, RR_dict=RR_dict)
    tags = list(sorted(tags_dict.values()))
    tags2_rxn_num = {v: k for k, v in tags_dict.items()}
    if debug:
        print(tags)
    # Get stiochiometry of reactions for family
    RR_dict_fam_stioch = AC.get_stioch_for_family_reactions(fam=fam,
                                                            RR_dict=RR_dict, Mechanism=Mechanism)
    # --- Get data for Ox loss for famiy
    ars = AC.get_fam_prod_loss_for_tagged_mechanism(RR_dict=RR_dict, wd=wd,
                                                    Var_rc=Var_rc, Data_rc=Data_rc, fam=fam, ref_spec=ref_spec, tags=tags,
                                                    tags2_rxn_num=tags2_rxn_num, RR_dict_fam_stioch=RR_dict_fam_stioch,
                                                    weight_by_num_molecules=weight_by_num_molecules, rm_strat=rm_strat)
    # Combine to a single array
    arr = np.array(ars)
    if debug:
        print(arr.shape)
    # --- Split reactions by family
    # Get families for tags
    fam_dict = AC.get_Ox_family_tag_based_on_reactants(fam=fam, tags=tags_dict,
                                                       RR_dict=RR_dict, GC_version=Data_rc['GC_version'])
    if debug:
        print(fam_dict)
    # Get indices of array for family.
    sorted_fam_names = list(sorted(set(fam_dict.values())))
    if debug:
        print sorted_fam_names, len(sorted_fam_names)
    sorted_fam_names = [
        'Photolysis', 'HO$_{\\rm x}$', 'NO$_{\\rm x}$',
        'Chlorine', 'Cl+Br', 'Bromine', 'Br+I', 'Cl+I', 'Iodine',
    ]
    if debug:
        print(sorted_fam_names, len(sorted_fam_names))
    fam_tag = [fam_dict[i] for i in tags]
    fam_ars = []
    for fam_ in sorted_fam_names:
        # get indices for routes of family
        fam_ind = [n for n, i in enumerate(fam_tag) if (i == fam_)]
        if debug:
            print(fam_ind, len(fam_ind))
        # Select these ...
        fam_ars += [arr[fam_ind, ...]]
    # Recombine and sum by family...
    if debug:
        print([i.shape for i in fam_ars], len(fam_ars))
    arr = np.array([i.sum(axis=0) for i in fam_ars])
    if debug:
        print(arr.shape)
    # --- Plot up as a stack-plot...
    # normalise to total and conver to % (*100)
    arr = (arr / arr.sum(axis=0)) * 100
    # add zeros array to beginning (for stack/area plot )
    arr_ = np.vstack((np.zeros((1, arr.shape[-1])), arr))
    # Setup figure?
    fig, ax = plt.subplots(figsize=(9, 6), dpi=Var_rc['dpi'], \
                           # loval variable settings
                           facecolor='w', edgecolor='w')
    # Plot by family
    for n, label in enumerate(sorted_fam_names):
        # print out some summary stats
        print n, label, arr[:n, 0].sum(axis=0), arr[:n+1, 0].sum(axis=0),
        print arr[:n, :].sum(), arr[:n+1, :].sum()
        print [i.shape for i in Data_rc['alt'], arr]
        # fill between X and Y.
        plt.fill_betweenx(Data_rc['alt'], arr[:n, :].sum(axis=0),
                          arr[:n+1, :].sum(axis=0),
                          color=Var_rc['cmap'](1.*n/len(sorted_fam_names)))
        # plot the line too
        plt.plot(arr[:n, :].sum(axis=0), Data_rc['alt'], label=label,
                 color=Var_rc['cmap'](1.*n/len(sorted_fam_names)), alpha=0,
                 lw=Var_rc['lw'],)
    # Beautify the plot
    plt.xlim(0, 100)
    xlabel = u'% of total O$_{\\rm x}$ loss'
    plt.xlabel(xlabel, fontsize=Var_rc['f_size']*.75)
    plt.yticks(fontsize=Var_rc['f_size']*.75)
    plt.xticks(fontsize=Var_rc['f_size']*.75)
    plt.ylabel('Altitude (km)', fontsize=Var_rc['f_size']*.75)
    leg = plt.legend(loc='upper center', fontsize=Var_rc['f_size'])
    # Update lengnd line sizes ( + update line sizes)
    for legobj in leg.legendHandles:
        legobj.set_linewidth(Var_rc['lw']/2)
        legobj.set_alpha(1)
    plt.ylim(Data_rc['alt'][0], Data_rc['alt'][-1])
    # Limit plot y axis to 12km?
    if limit_plotted_alititude:
        plt.ylim(Data_rc['alt'][0], 12)
    plt.show()


def calc_fam_loss_by_route(wd=None, fam='LOx', ref_spec='O3', region=None,
                           rm_strat=True, Mechanism='Halogens', verbose=True, debug=False):
    """
    Build an Ox budget table like table 4 in Sherwen et al 2016b

    Parameters
    -------
    fam (str): tagged family to track (already compiled in KPP mechanism)
    ref_spec (str): reference species to normalise to
    region (str): region to consider (by masking all but this location)
    wd (str): working directory ("wd") of model output
    rm_strat (boolean): (fractionally) replace values in statosphere with zeros
    debug, verbose (bool): switches to turn on/set verbosity of output to screen

    Returns
    -------
    (None)

    Notes
    -----
     - AC_tools includes equivlent functions for smvgear mechanisms
    """
    # --- Get key model variables, model settings, etc
    # Get locations of model output/core
    Var_rc, Data_rc = func_settings(full_vertical_grid=True, wd=wd)
    wd = Var_rc['wd']
    assert os.path.exists(wd), 'working directory not found @: {}'.format(wd)
    CODE_wd = '{}/../code/KPP/{}/'.format(wd, Mechanism)
    assert os.path.exists(CODE_wd), 'code directory not found @: ' + CODE_wd
    # Get data variables shared for
    full_vertical_grid = False
    Var_rc, Data_rc = func_settings(full_vertical_grid=full_vertical_grid,
                                    wd=wd)
    # Get reaction dictionary
    RR_dict = AC.get_dict_of_KPP_mech(wd=CODE_wd,
                                      GC_version=Data_rc['GC_version'], Mechanism=Mechanism)
    if debug:
        print(len(RR_dict), [RR_dict[i] for i in RR_dict.keys()[:5]])
    # Get tags for family
    tags_dict = AC.get_tags4_family(fam=fam, wd=CODE_wd, RR_dict=RR_dict)
    tags = list(sorted(tags_dict.values()))
    tags2_rxn_num = {v: k for k, v in tags_dict.items()}
    if debug:
        print(tags)
    # Get stiochiometry of reactions for family
    RR_dict_fam_stioch = AC.get_stioch_for_family_reactions(fam=fam,
                                                            RR_dict=RR_dict, Mechanism=Mechanism)
    # --- Extract data for Ox loss for family from model
    ars = AC.get_fam_prod_loss_for_tagged_mechanism(RR_dict=RR_dict,
                                                    tags=tags, rm_strat=rm_strat,
                                                    Var_rc=Var_rc, Data_rc=Data_rc, wd=wd, fam=fam, ref_spec=ref_spec,
                                                    tags2_rxn_num=tags2_rxn_num, RR_dict_fam_stioch=RR_dict_fam_stioch,
                                                    weight_by_num_molecules=False)
    # Get families that tags belong to
    fam_dict = AC.get_Ox_family_tag_based_on_reactants(fam=fam, tags=tags_dict,
                                                       RR_dict=RR_dict, GC_version=Data_rc['GC_version'])
    # Get indices of array for family.
#    sorted_fam_names = list(sorted(set(fam_dict.values())))
    sorted_fam_names = ['Photolysis', 'HO$_{\\rm x}$', 'NO$_{\\rm x}$']
    halogen_fams = ['Chlorine', 'Cl+Br', 'Bromine', 'Br+I', 'Cl+I', 'Iodine', ]
    sorted_fam_names += halogen_fams

    # --- Do analysis on model output
    # sum the total mass fluxes for each reaction
    ars = [i.sum() for i in ars]
    # Sum all the routes
    total = np.array(ars).sum()
    # Create a dictionary of values of interest
    dict_ = {
        'Total flux': [i.sum(axis=0) for i in ars],
        'Total of flux (%)': [i.sum(axis=0)/total*100 for i in ars],
        'Family': [fam_dict[i] for i in tags],
        'rxn #': [tags2_rxn_num[i] for i in tags],
        'rxn str': [RR_dict[tags2_rxn_num[i]] for i in tags],
        'stoich': [RR_dict_fam_stioch[tags2_rxn_num[i]] for i in tags],
        'tags': tags,
    }
    # Create pandas dataframe
    df = pd.DataFrame(dict_)
    # Sort the data and have a look...
    df = df.sort_values('Total flux', ascending=False)
    print df.head()
    # Sort values again and save...
    df = df.sort_values(['Family', 'Total flux'], ascending=False)
    print df.head()
    df.to_csv('test_Ox.csv')
    # Now select the most important routes
    df_sum = pd.DataFrame()
    grp = df[['Family', 'Total flux']].groupby('Family')
    total = grp.sum().sum()
    # Print the contribution by family to screen
    print(grp.sum() / total * 100)
    # Print the contribution of all the halogen routes
    hal_LOx = (grp.sum().T[halogen_fams].sum().sum() / total * 100).values[0]
    print('Total contribution of halogens is: {:.2f} %'.format(hal_LOx))


def func_settings(wd=None, filename=None, full_vertical_grid=True):
    """ Function to store generic/shared variables/data """
    # - I/O settings
    # Setup dictionary.
    Var_rc = AC.get_default_variable_dict(
        full_vertical_grid=full_vertical_grid)
    # Add plotting settings to variable dictionary object ("Var_rc")
    Var_rc['cmap'] = plt.cm.jet
    Var_rc['f_size'] = 10
    Var_rc['dpi'] = 320
    Var_rc['dpi'] = 160
    Var_rc['lw'] = 16
    Var_rc['limit_vertical_dim'] = True
    if not isinstance(wd, type(None)):
        Var_rc['wd'] = wd
    # - Data settings (list variables to extract... )
    var_list = [
        'generic_4x5_wd', 'months', 'years', 'datetimes', 'output_freq',
        'output_vertical_grid', 's_area', 'vol', 't_ps', 'n_air', 'molecs',
        'alt'
    ]
    Data_rc = AC.get_shared_data_as_dict(Var_rc=Var_rc, var_list=var_list)
    # Return dictionaries
    return Var_rc, Data_rc


if __name__ == "__main__":
    main()
