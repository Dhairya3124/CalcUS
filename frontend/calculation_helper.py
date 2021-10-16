'''
This file of part of CalcUS.

Copyright (C) 2020-2021 Raphaël Robidas

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''


from .constants import *
import string

def get_abs_method(method):
    for m in SYN_METHODS.keys():
        if method.lower() in SYN_METHODS[m] or method.lower() == m:
            return m
    return -1

def get_abs_basis_set(basis_set):
    for bs in SYN_BASIS_SETS.keys():
        if basis_set.lower() in SYN_BASIS_SETS[bs] or basis_set.lower() == bs:
            return bs
    return -1

def get_abs_solvent(solvent):
    for solv in SYN_SOLVENTS.keys():
        if solvent.lower() in SYN_SOLVENTS[solv] or solvent.lower() == solv:
            return solv
    return -1

def get_method(method, software):
    abs_method = get_abs_method(method)
    if abs_method == -1:
        return method
    return SOFTWARE_METHODS[software][abs_method]

def get_basis_set(basis_set, software):
    abs_basis_set = get_abs_basis_set(basis_set)
    if abs_basis_set == -1:
        return basis_set
    return SOFTWARE_BASIS_SETS[software][abs_basis_set]

def get_solvent(solvent, software, solvation_model="SMD"):
    abs_solvent = get_abs_solvent(solvent)

    if abs_solvent == -1:
        return solvent

    if software == "ORCA" and abs_solvent == "n-octanol":
        #Weird exception in ORCA
        if solvation_model == "SMD":
            return "1-octanol"
        elif solvation_model == "CPCM":
            return "octanol"
        #Note that ch2cl2 is a valid keyword for SMD, although not listed in the manual

    return SOFTWARE_SOLVENTS[software][abs_solvent]

def clean_xyz(xyz):
    return ''.join([x if x in string.printable else ' ' for x in xyz])

