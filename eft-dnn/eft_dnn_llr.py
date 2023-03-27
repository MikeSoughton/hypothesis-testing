#!/usr/bin/env python3

"""
    Script to take a pdf of prob(eft) and compute the log-likelihood ratio to
    perform a hypothesis test. Outputs plot of seperation significance against
    LHC luminosity for a given probability threshold cut.
    __author__ = "Michael Soughton", "Charanjit Kaur Khosa", "Veronica Sanz"
    __email__ =
"""

import numpy as np
import matplotlib.pyplot as plt
from numpy import log
import scipy.optimize
from scipy.stats import norm
from scipy import integrate
import random
import os
from keras.layers import Input, Dense, Lambda, Flatten, Reshape
from keras.models import Model
from keras import backend as K
from keras import metrics

import seaborn as sns; sns.set(style="white", color_codes=True)

# =========================== Take in arguments ================================
import argparse

parser = argparse.ArgumentParser(description='These are the arguments that will be passed to the script')

parser.add_argument("--pcut",
                    type=float,
                    default=0,
                    help="float: The cut point of the probabilities, between 0 and 1. Default is 0.")

parser.add_argument("--ntoys",
                    type=int,
                    default=1000,
                    help="int: The number of toy events to use. Default is 1000, but use more for better accuracy.")

parser.add_argument("--ext_num",
                    type=str,
                    default=999,
                    help="str: The extension number for the output files. Should take the form of 00x, 0xy, xyz.")

args = parser.parse_args()

print("Pcut = " + str(args.pcut) + "ntoys = " + str(args.ntoys) + ", extension number = " + str(args.ext_num))

# =========================== Load pdf data ====================================

dnn_outputs = 'dnn_outputs/'

#sm_sample = np.loadtxt(dnn_outputs + "vh_chw_zero.txt", unpack=True)
#eft_sample = np.loadtxt(dnn_outputs + "vh_chw_zp005.txt", unpack=True)
sm_sample = np.loadtxt(dnn_outputs + "vh_chw_zero_1kbootstrap001.txt", unpack=True)
eft_sample = np.loadtxt(dnn_outputs + "vh_chw_zp005_1kbootstrap001.txt", unpack=True)

# Rescale probabilities so that they range form 0 - 1 instead of ~0.46 - 1
#sample_minimum = min(np.min(sm_sample),np.min(eft_sample))
sample_minimum = 0.4688633680343628

print("Sample minimum", sample_minimum)

sm_sample = (sm_sample - sample_minimum)/(1. - sample_minimum)
eft_sample = (eft_sample - sample_minimum)/(1. - sample_minimum)

# =========================== Find and plot pdf ================================
extension = 'with_poisson_' + str(args.pcut) + 'Pcut_' + str(int(args.ntoys/1000)) + 'ktoys' + str(args.ext_num)
plot_dir = 'test62Plots/' + extension + '/'
array_dir = 'test62arrays/'
fig_specification = ''
os.makedirs(plot_dir, exist_ok=True)
os.makedirs(array_dir, exist_ok=True)
plt.close("all")

nbins = 50
min_bin = min(np.min(sm_sample), np.min(eft_sample))
max_bin = min(np.max(sm_sample), np.max(eft_sample))

# This is just a plot for visualisation purposes and is not necessary for the code
fig, ax = plt.subplots(1,1, figsize = (8,8))
ax.hist(sm_sample, bins = np.linspace(0, max_bin, nbins), label = 'SM', density = True, alpha = 0.5, color = 'green')
ax.hist(eft_sample, bins = np.linspace(0, max_bin, nbins), label = 'EFT', density = True, alpha = 0.5)
ax.legend()
ax.set_xlabel('P(EFT Jet)')
ax.set_title("Binary classification for SM vs EFT")
ax.set_xlim()
#plt.savefig(plot_dir + "Firstplot" + fig_specification + ".png")

# ============================ Setup pdfs to be used ===========================

# Function to produce pdf
def get_pdf(recons_error, min_bin=0, max_bin=1, nbins=20):
    histo,bins = np.histogram(recons_error, bins=np.linspace(min_bin, max_bin, nbins), density = True)
    return histo, bins


def get_histo(recons_error, min_bin=0, max_bin=1, nbins=20):
    histo, bins= np.histogram(recons_error, bins=np.linspace(min_bin, max_bin, nbins), density = False)
    return histo, bins

# Get reference pdf and bins
sm_reference_pdf, sm_bins = get_pdf(sm_sample, 0, 1, nbins)
eft_reference_pdf, eft_bins = get_pdf(eft_sample, 0, 1, nbins)

sm_reference_hist,_ = get_histo(sm_sample, 0, 1, nbins)
eft_reference_hist,_ = get_histo(eft_sample, 0, 1, nbins)

# Center bins
sm_bins_centered = np.zeros(len(sm_bins) - 1)
for i in range(len(sm_bins) - 1):
    sm_bins_centered[i] = (sm_bins[i] + sm_bins[i+1])/2

eft_bins_centered = np.zeros(len(eft_bins) - 1)
for i in range(len(eft_bins) - 1):
    eft_bins_centered[i] = (eft_bins[i] + eft_bins[i+1])/2
mixed_bins_centered = eft_bins_centered

# Check that the pdf we will use in the computation is the same as the one used for visualisation
fig, ax = plt.subplots(1,1, figsize = (8,8))
#plt.hist(sm_reference_pdf,sm_bins)
plt.plot(sm_bins_centered , sm_reference_pdf)
plt.plot(eft_bins_centered , eft_reference_pdf)
ax.legend()
ax.set_xlabel('P(EFT Jet)')
ax.set_title("Binary classification for SM vs EFT")
ax.set_xlim()
#plt.savefig(plot_dir + "secondplot" + fig_specification + ".png")

# Function to drop zeros within the pdf since log-likelihood will return NaN in such cases
def drop_zeros(sm_pdf, eft_pdf):
    # Drop values from histograms where test histogram equal to 0
    idx_to_keep = np.where(sm_pdf != 0)[0]
    sm_pdf = sm_pdf[idx_to_keep]
    eft_pdf = eft_pdf[idx_to_keep]

    # # Drop values from histograms where anomaly histogram equal to 0
    idx_to_keep = np.where(eft_pdf != 0)[0]
    sm_pdf = sm_pdf[idx_to_keep]
    eft_pdf = eft_pdf[idx_to_keep]

    return sm_pdf, eft_pdf

# In the sm and eft probs pdf there are actually no zeros (at least for the number of bins we use)
#sm_reference_pdf, eft_reference_pdf = drop_zeros(sm_reference_pdf, eft_reference_pdf)

# Center bins
sm_bins_centered = np.zeros(len(sm_bins) - 1)
for i in range(len(sm_bins) - 1):
    sm_bins_centered[i] = (sm_bins[i] + sm_bins[i+1])/2

eft_bins_centered = np.zeros(len(eft_bins) - 1)
for i in range(len(eft_bins) - 1):
    eft_bins_centered[i] = (eft_bins[i] + eft_bins[i+1])/2


#sm_cross_section = 23.941
#eft_cross_section = 28
sm_cross_section = 0.014009*1000
eft_cross_section = 0.017125*1000
eft_to_sm_ratio = eft_cross_section/sm_cross_section
#eft_to_sm_ratio = 0.0005

#mixed_sample, mixed_reference_pdf, mixed_bins = mix_pdfs(sm_sample, eft_bins_centered, eft_reference_hist, eft_to_sm_ratio)
mixed_sample = eft_sample
mixed_reference_pdf = eft_reference_pdf
mixed_bins = eft_bins
# ====================== Find and plot mixed pdf ===============================

# This is just a plot for visualisation purposes and is not necessary for the code
fig, ax = plt.subplots(1,1, figsize = (8,8))
#ax.hist(sm_sample, bins = np.linspace(0, max_bin, nbins), label = 'SM', density = True, alpha = 0.5)
ax.hist(eft_sample, bins = np.linspace(0, max_bin, nbins), label = 'EFT', density = True, alpha = 0.5)
ax.hist(mixed_sample, bins = np.linspace(0, max_bin, nbins), label = 'Mixed', density = True, alpha = 0.5)
ax.legend()
ax.set_xlabel('P(EFT Jet)')
ax.set_title("Binary classification for SM vs EFT")
ax.set_xlim()
plt.savefig(plot_dir + "pdf_plot" + fig_specification + ".pdf")


# This is just a plot for visualisation purposes and is not necessary for the code
fig, ax = plt.subplots(1,1, figsize = (8,8))
#ax.hist(sm_sample, bins = np.linspace(0, max_bin, nbins), label = 'SM', density = True, alpha = 0.5)
ax.hist(eft_sample, bins = np.linspace(0, max_bin, nbins), label = 'EFT', density = True, alpha = 0.5)
ax.hist(mixed_sample, bins = np.linspace(0, max_bin, nbins), label = 'Mixed', density = True, alpha = 0.5)
ax.legend()
ax.set_xlabel('P(EFT Jet)')
ax.set_title("Binary classification for SM vs EFT")
ax.set_xlim()
#plt.savefig(plot_dir + "pdfs" + fig_specification + ".pdf")

# New plots
# This is just a plot for visualisation purposes and is not necessary for the code
#fig, ax = plt.subplots(1,1, figsize = (8,8))
fig = plt.figure(figsize = (6,6))
ax=fig.add_axes([0.13,0.11,0.8,0.8])
#ax.hist(eft_sample, bins = np.linspace(0, max_bin, nbins), label = 'EFT', density = True, alpha = 0.7)
ax.hist(sm_sample, bins = np.linspace(0, max_bin, nbins), label = 'SM', density = True, alpha = 0.7, color = 'green')
ax.hist(mixed_sample, bins = np.linspace(0, max_bin, nbins), label = 'EFT', density = True, alpha = 0.7)
l1=ax.legend(loc="upper center",fontsize=14)
ax.set_xlabel(r'$P(\mathrm{EFT})$',fontsize=14)
ax.set_ylabel(r'PDF',fontsize=14)
ax.set_title("SM vs EFT",fontsize=14)
ax.set_xlim()
plt.savefig(plot_dir + "pdfs" + fig_specification + ".pdf")

fig = plt.figure(figsize = (6,6))
ax=fig.add_axes([0.13,0.11,0.8,0.8])
#ax.hist(eft_sample, bins = np.linspace(0, max_bin, nbins), label = 'EFT', density = True, alpha = 0.7)
ax.hist(sm_sample, bins = np.linspace(0, max_bin, nbins), label = 'SM', density = True, alpha = 0.7, color = 'green')
ax.hist(mixed_sample, bins = np.linspace(0, max_bin, nbins), label = 'EFT', density = True, alpha = 0.7)
l1=ax.legend(loc="upper center",fontsize=14)
ax.set_xlabel(r'$P(\mathrm{EFT})$',fontsize=14)
ax.set_ylabel(r'PDF',fontsize=14)
ax.set_title("SM vs EFT",fontsize=14)
ax.set_xlim()
ax.set_yscale('log')
plt.savefig(plot_dir + "jet_nsigmaVsNtop_0Pcut" + fig_specification + ".pdf")

# Cut PDF
cut_point = 0.5
#eft_sample_cut = np.stack(list(eft_sample))
sm_sample_cut = np.stack(list(sm_sample))
mixed_sample_cut = np.stack(list(mixed_sample))
#eft_sample_cut = np.delete(eft_sample_cut,np.where(eft_sample_cut < cut_point)[0])
sm_sample_cut = np.delete(sm_sample_cut,np.where(sm_sample_cut < cut_point)[0])
mixed_sample_cut = np.delete(mixed_sample_cut,np.where(mixed_sample_cut < cut_point)[0])

fig = plt.figure(figsize = (6,6))
ax=fig.add_axes([0.13,0.11,0.8,0.8])
#ax.hist(eft_sample_cut, bins = np.linspace(0, max_bin, nbins), label = 'EFT', density = True, alpha = 0.7)
ax.hist(sm_sample_cut, bins = np.linspace(0, max_bin, nbins), label = 'SM', density = True, alpha = 0.7)
ax.hist(mixed_sample_cut, bins = np.linspace(0, max_bin, nbins), label = 'SM + EFT', density = True, alpha = 0.7)
l1=ax.legend(loc="upper center",fontsize=14)
ax.add_artist(l1)
ax.set_xlabel(r'$P(\mathrm{EFT})$',fontsize=14)
ax.set_ylabel(r'PDF',fontsize=14)
ax.set_title("SM vs SM + EFT",fontsize=14)
ax.set_xlim(0,1)
#ax.set_yscale('log')
plt.savefig(plot_dir + "pdfs" + fig_specification + ".pdf")

fig = plt.figure(figsize = (6,6))
ax=fig.add_axes([0.13,0.11,0.8,0.8])
#ax.hist(eft_sample_cut, bins = np.linspace(0, max_bin, nbins), label = 'EFT', density = True, alpha = 0.7)
ax.hist(sm_sample_cut, bins = np.linspace(0, max_bin, nbins), label = 'SM', density = True, alpha = 0.7)
ax.hist(mixed_sample_cut, bins = np.linspace(0, max_bin, nbins), label = 'SM + EFT', density = True, alpha = 0.7)
l1=ax.legend(loc="upper center",fontsize=14)
ax.add_artist(l1)
ax.set_xlabel(r'$P(\mathrm{EFT})$',fontsize=14)
ax.set_ylabel(r'PDF',fontsize=14)
ax.set_title("SM vs SM + EFT",fontsize=14)
ax.set_xlim(0,1)
ax.set_yscale('log')
plt.savefig(plot_dir + "pdfs" + fig_specification + ".pdf")






# ================= Define some more fucntions that will be used ===============

# Function to fit Gaussian to data
def fit_gaussian(xdata, ydata, xbins):
    # Find parameters of Gaussian; amplitude, mean, stdev
    amp = np.max(ydata)
    mu = np.mean(xdata)
    sigma = np.std(xdata)
    print(amp, mu, sigma)

    # Define the form of the Gaussian
    def gaussian(x, amplitude, mean, stddev):
        return amplitude * np.exp(-((x - mean) / 4 / stddev)**2)

    # Fit parameters for the Gaussian defined above from the data. p0 are initial guesses
    popt, _ = scipy.optimize.curve_fit(gaussian, xbins, ydata, p0 = [amp, mu, sigma])

    # Now get the Gaussian curve with those fitted parameters
    fitted_gaussian = gaussian(xbins, *popt)
    return fitted_gaussian, popt

# Function to run over pdfs and compute sum log likelihoods to obtain alpha
def get_alpha(LLRsm_list, LLReft_list, LLRsm_histo, LLRsm_bins, LLReft_histo, LLReft_bins):
    # Recenter bins
    LLRsm_binscenters = np.array([0.5 * (LLRsm_bins[i] + LLRsm_bins[i+1]) for i in range(len(LLRsm_bins)-1)])
    LLReft_binscenters = np.array([0.5 * (LLReft_bins[i] + LLReft_bins[i+1]) for i in range(len(LLReft_bins)-1)])

    # Get parameters for Gaussian fit
    _, test_gaus_params = fit_gaussian(LLRsm_list, LLRsm_histo, LLRsm_binscenters)
    _, anomaly_gaus_params = fit_gaussian(LLReft_list, LLReft_histo, LLReft_binscenters)

    test_amplitude = test_gaus_params[0]
    test_mean = test_gaus_params[1]
    test_stdev = abs(test_gaus_params[2]) # abs since for some weird numerical reason stdev can be -ve. (it does not matter since it is squared but it makes me feel uncomfortable unless it is +ve)

    anomaly_amplitude = anomaly_gaus_params[0]
    anomaly_mean = anomaly_gaus_params[1]
    anomaly_stdev = abs(anomaly_gaus_params[2])

    # Integrate over Gaussian distribution with different lambda_cut as limits
    # to get alpha for which alpha = beta
    def integrand(x, amplitude, mean, stdev):
        return amplitude * np.exp(-((x - mean) / 4 / stdev)**2)


    #lam_cut_potential_values = np.linspace(-200, -80, 1000)

    # min and max lamda values (would be infinity but scipy.integrate.quad breaks when using scipy.inf)
    print("====================== VALUES ================================")
    print(test_amplitude, test_mean, test_stdev, anomaly_amplitude, anomaly_mean, anomaly_stdev)
    min_lam = anomaly_mean - 50*np.average((test_stdev, anomaly_stdev))
    max_lam = test_mean + 50*np.average((test_stdev, anomaly_stdev))
    print(min_lam, max_lam)

    lam_cut_potential_values = np.linspace(anomaly_mean - 20*np.average((test_stdev, anomaly_stdev)), test_mean + 20*np.average((test_stdev, anomaly_stdev)), 1000)

    # Alpha and beta normalisations
    alpha_normalisation ,alpha_normalisation_error = integrate.quad(integrand,min_lam,max_lam,args=(test_amplitude, test_mean, test_stdev))
    beta_normalisation ,beta_normalisation_error = integrate.quad(integrand,min_lam,max_lam,args=(anomaly_amplitude, anomaly_mean, anomaly_stdev))
    print("========NORMALISATION:======================")
    print("HELLO")
    print(alpha_normalisation, beta_normalisation)

    # Integrate from increasing values of lam_cut to find alpha which is closest to beta
    alpha_list = []
    beta_list = []
    alpha_beta_diff_list = []
    for i,lam_cut in enumerate(lam_cut_potential_values):
        alpha_integral1 ,alpha_integral1_error = integrate.quad(integrand,min_lam,lam_cut,args=(test_amplitude, test_mean, test_stdev))
        alpha = alpha_integral1/alpha_normalisation
        alpha_list.append(alpha)

        beta_integral1 ,beta_integral1_error = integrate.quad(integrand,lam_cut,max_lam,args=(anomaly_amplitude, anomaly_mean, anomaly_stdev))
        beta = beta_integral1/beta_normalisation

        # Create a list of the difference between alpha and beta - we will search for the value that is closest to zero
        alpha_beta_diff = abs(alpha - beta)
        alpha_beta_diff_list.append(alpha_beta_diff)
        beta_list.append(beta)
        #print(i, lam_cut, alpha_integral1, alpha, beta_integral1, beta, alpha_beta_diff)

    # Get the value of lam_cut for which alpha is closest to beta (approx of alpha = beta)
    closest_index = alpha_beta_diff_list.index(min(alpha_beta_diff_list))
    lam_cut = lam_cut_potential_values[closest_index]

    # Get the value of alpha for which alpha is closest to beta (approx of alpha = beta)
    alpha = alpha_list[closest_index]

    return alpha

def get_alpha_exact(LLRsm_list, LLReft_list, LLRsm_histo, LLRsm_bins, LLReft_histo, LLReft_bins):
    # Loop through all bins, calculating the area under LLR hist A and B and find the bin where areas are most equal
    #LLRA_values, LLRA_bins,_ = plt.hist(LLRsm_list, bins = np.linspace(min_llr, max_llr, 100), label = 'SM', alpha = 0.5)
    #LLRB_values, LLRB_bins,_ = plt.hist(LLReft_list, bins = np.linspace(min_llr, max_llr, 100), label = 'EFT', alpha = 0.5)

    LLRA_values,LLRA_bins = LLRsm_histo, LLRsm_bins
    LLRB_values,LLRB_bins = LLReft_histo, LLReft_bins

    alpha_list = []
    beta_list = []
    alpha_beta_diff_list = []
    # A and B share the same bins
    # A is to the left of B
    for i, bin in enumerate(LLRA_bins):
        alpha = sum(np.diff(LLRA_bins[i:])*LLRA_values[i:])/sum(np.diff(LLRA_bins)*LLRA_values)
        beta = sum(np.diff(LLRB_bins[:(i+2)])*LLRB_values[:(i+1)])/sum(np.diff(LLRB_bins)*LLRB_values)
        alpha_list.append(alpha)
        beta_list.append(beta)

        alpha_beta_diff = abs(alpha - beta)
        alpha_beta_diff_list.append(alpha_beta_diff)

    # Get the value of lam_cut for which alpha is closest to beta (approx of alpha = beta)
    closest_index = alpha_beta_diff_list.index(min(alpha_beta_diff_list))
    bin_cut = LLRA_bins[closest_index]

    # Get the value of alpha for which alpha is closest to beta (approx of alpha = beta)
    alpha = alpha_list[closest_index]

    return alpha

def get_alpha_no_beta(LLRqcd_list, LLRtop_list, LLRqcd_histo, LLRqcd_bins, LLRtop_histo, LLRtop_bins):
    # Recenter bins
    LLRqcd_binscenters = np.array([0.5 * (LLRqcd_bins[i] + LLRqcd_bins[i+1]) for i in range(len(LLRqcd_bins)-1)])
    LLRtop_binscenters = np.array([0.5 * (LLRtop_bins[i] + LLRtop_bins[i+1]) for i in range(len(LLRtop_bins)-1)])

    # Get parameters for Gaussian fit
    _, test_gaus_params = fit_gaussian(LLRqcd_list, LLRqcd_histo, LLRqcd_binscenters)
    _, anomaly_gaus_params = fit_gaussian(LLRtop_list, LLRtop_histo, LLRtop_binscenters)

    test_amplitude = test_gaus_params[0]
    test_mean = test_gaus_params[1]
    test_stdev = abs(test_gaus_params[2]) # abs since for some weird numerical reason stdev can be -ve. (it does not matter since it is squared but it makes me feel uncomfortable unless it is +ve)

    anomaly_amplitude = anomaly_gaus_params[0]
    anomaly_mean = anomaly_gaus_params[1]
    anomaly_stdev = abs(anomaly_gaus_params[2])

    # Integrate over Gaussian distribution with different lambda_cut as limits
    # to get alpha for which alpha = beta
    def integrand(x, amplitude, mean, stdev):
        return amplitude * np.exp(-((x - mean) / 4 / stdev)**2)


    #lam_cut_potential_values = np.linspace(-200, -80, 1000)

    # min and max lamda values (would be infinity but scipy.integrate.quad breaks when using scipy.inf)
    print("====================== VALUES ================================")
    print(test_amplitude, test_mean, test_stdev, anomaly_amplitude, anomaly_mean, anomaly_stdev)
    min_lam = anomaly_mean - 50*np.average((test_stdev, anomaly_stdev))
    max_lam = test_mean + 50*np.average((test_stdev, anomaly_stdev))
    print(min_lam, max_lam)

    lam_cut_potential_values = np.linspace(anomaly_mean - 20*np.average((test_stdev, anomaly_stdev)), test_mean + 20*np.average((test_stdev, anomaly_stdev)), 100000)

    # Alpha and beta normalisations
    alpha_normalisation ,alpha_normalisation_error = integrate.quad(integrand,min_lam,max_lam,args=(test_amplitude, test_mean, test_stdev))
    beta_normalisation ,beta_normalisation_error = integrate.quad(integrand,min_lam,max_lam,args=(anomaly_amplitude, anomaly_mean, anomaly_stdev))
    print("========NORMALISATION:======================")
    print("HELLO")
    print(alpha_normalisation, beta_normalisation)

    # Now take lam cut to be mean of mixed LLR
    lam_cut = np.mean(LLRtop_list)
    print("LAM CUT",lam_cut)
    alpha_integral1 ,alpha_integral1_error = integrate.quad(integrand,min_lam,lam_cut,args=(test_amplitude, test_mean, test_stdev))
    alpha = alpha_integral1/alpha_normalisation

    return alpha

def get_alpha_exact(LLRqcd_list, LLRtop_list, LLRqcd_histo, LLRqcd_bins, LLRtop_histo, LLRtop_bins):
    # Loop through all bins, calculating the area under LLR hist A and B and find the bin where areas are most equal
    #LLRA_values, LLRA_bins,_ = plt.hist(LLRqcd_list, bins = np.linspace(min_llr, max_llr, 100), label = 'QCD', alpha = 0.5)
    #LLRB_values, LLRB_bins,_ = plt.hist(LLRtop_list, bins = np.linspace(min_llr, max_llr, 100), label = 'Top', alpha = 0.5)

    LLRA_values,LLRA_bins = LLRqcd_histo, LLRqcd_bins
    LLRB_values,LLRB_bins = LLRtop_histo, LLRtop_bins

    alpha_list = []
    beta_list = []
    alpha_beta_diff_list = []
    # A and B share the same bins
    # A is to the left of B
    for i, bin in enumerate(LLRA_bins):
        alpha = sum(np.diff(LLRA_bins[i:])*LLRA_values[i:])/sum(np.diff(LLRA_bins)*LLRA_values)
        beta = sum(np.diff(LLRB_bins[:(i+2)])*LLRB_values[:(i+1)])/sum(np.diff(LLRB_bins)*LLRB_values)
        alpha_list.append(alpha)
        beta_list.append(beta)

        alpha_beta_diff = abs(alpha - beta)
        alpha_beta_diff_list.append(alpha_beta_diff)

    # Get the value of lam_cut for which alpha is closest to beta (approx of alpha = beta)
    closest_index = alpha_beta_diff_list.index(min(alpha_beta_diff_list))
    bin_cut = LLRA_bins[closest_index]

    # Get the value of alpha for which alpha is closest to beta (approx of alpha = beta)
    alpha = alpha_list[closest_index]

    return alpha


# Function to get standard deviations of seperation from alpha:
# For the found value of alpha, find the corresponding number of standard
# deviations n by solving
# alpha = (1/sqrt(2 pi)) * int_n^inf exp(-x^2/2) dx
# Note that this is the one-sided defintion and i don't think that it is well
# defined for alpha < 0.5, though the correct result could be obtained for alpha > 0.5
# if you do alpha -> 1 - alpha
def get_nstdevs(alpha):
    # The integrand
    def integrand(x):
        return np.exp(-x**2/2)

    # The function to solve for - this is the above equation rearranged
    # Max number of standard deviation to integrate up to (a number -> infity)
    # For some reason n ~> 10000 gives bad integration but 1000 is more than enough
    n_max = 1000
    def func(n):
        integral,error = integrate.quad(integrand, n, n_max)
        return integral - alpha*np.sqrt(2.0*np.pi)

    # Solve
    n_estimate = 1.0
    sol = scipy.optimize.fsolve(func, n_estimate)

    return sol[0]

# ============== Define the log-likelihood sampling procedure===================

# Function to sample from toy experiments and return the log likelihoods for sm
# and eft if they were to be sampled from either eft or sm
def sample_ll_from_toys(pdfA, pdfA_bins, pdfB, N_toys=10000, N_toy_events=50):
    # For each toy experiment we will find the LLR
    toy_log_likelihood_sum_listA = []
    toy_log_likelihood_sum_listB = []

    for toy in range(N_toys):
        # Get sample bin values for pdf A, using pdf A as weights

        toy_histonum = random.choices(pdfA_bins, weights=pdfA, k=N_toy_events[toy])

        # Get the histogram of events corresponding to the randomly sampled bin/x-axis values
        # nbins must be the same as nbins of pdf
        nbins = len(pdfA) + 1
        min_P = np.min(pdfA_bins)
        #max_P = 1
        max_P = np.max(pdfA_bins) + np.diff(pdfA_bins)[0]/2 # Not sure why I have to do this to get the plot good, but I do
        toy_histo, _ = get_histo(toy_histonum, min_P, max_P, nbins)

        # Find the the likelihood for each toy by taking the product of all pdfs and take the log
        # Here I actually sum the log likelihood but when the product/sum is performed is irrelevant
        toy_log_likelihood_sumA = 0.0
        toy_log_likelihood_sumB = 0.0

        # For each event in the toy sample:
        for i in range(len(toy_histo)):
            if pdfA[i] > 0:
                # Find the likelihood and log-likelihood that one would get from the reference histogram
                LHA = pdfA[i] # this is not corresponding to the right value in the sample histo - well it is as long as nbins of reference histo and toy histo are the same
                LLA = -2*log(LHA)
                # Multiply the log-likelihood from the reference histogram by the number of samples in the corresponding bin, works since ll is a sum
                toy_log_likelihoodA = toy_histo[i]*LLA
                toy_log_likelihood_sumA += toy_log_likelihoodA
        toy_log_likelihood_sum_listA.append(toy_log_likelihood_sumA)

        for i in range(len(toy_histo)):
            if pdfB[i] > 0:
                # Find the likelihood and log-likelihood that one would get from the reference histogram
                LHB = pdfB[i] # this is not corresponding to the right value in the sample histo - well it is as long as nbins of reference histo and toy histo are the same
                LLB = -2*log(LHB)
                # Multiply the log-likelihood from the reference histogram by the number of samples in the corresponding bin, works since ll is a sum
                toy_log_likelihoodB = toy_histo[i]*LLB
                toy_log_likelihood_sumB += toy_log_likelihoodB
        toy_log_likelihood_sum_listB.append(toy_log_likelihood_sumB)
    print("MIN P", min_P)
    print("MAX P", max_P, np.diff(pdfA_bins)[0], nbins)
    return toy_log_likelihood_sum_listA, toy_log_likelihood_sum_listB

# ======================== Define the fucntion that will plot the log likelihood ratios ======================

def plot_llr(LLRsm, LLReft, anomaly_type, N_toys, N_toy_events, prob_threshold):

    # Plot and get histogram of -2ln(lambda) sampled from each toy experiment
    fig = plt.figure(figsize = (6,6))
    ax=fig.add_axes([0.13,0.14,0.8,0.8])
    min_llr = np.floor(min(np.min(LLRsm), np.min(LLReft)))
    max_llr = np.ceil(max(np.max(LLRsm), np.max(LLReft)))
    nbins = 100
    LLReft_histo, LLReft_bins, _ = ax.hist(LLReft, bins=np.linspace(min_llr,max_llr,100),label='SM + TOP', alpha = 0.7)
    LLRsm_histo, LLRsm_bins, _ = ax.hist(LLRsm, bins=np.linspace(min_llr,max_llr,100),label='SM',alpha = 0.7)
    # This requires centering the bins so that we can accurately fit a Gaussian
    LLRsm_binscenters = np.array([0.5 * (LLRsm_bins[i] + LLRsm_bins[i+1]) for i in range(len(LLRsm_bins)-1)])
    LLReft_binscenters = np.array([0.5 * (LLReft_bins[i] + LLReft_bins[i+1]) for i in range(len(LLReft_bins)-1)])

    #print("LLRsm_binscenters",LLRsm_binscenters)
    #print("LLRsm_histo",LLRsm_histo)

    # Fit a Gaussian
    LLRsm_gaus, _ = fit_gaussian(LLRsm, LLRsm_histo, LLRsm_binscenters)
    LLReft_gaus, _ = fit_gaussian(LLReft, LLReft_histo, LLReft_binscenters)

    # Plot the Gaussian
    ax.plot(LLRsm_binscenters, LLRsm_gaus, 'C1')
    ax.plot(LLReft_binscenters, LLReft_gaus, 'C0')
    ax.set_title(r'SM vs SM + EFT, $P_\mathrm{cut}(eft)$ = %s' % prob_threshold, fontsize=14)
    #ax.set_title(r'SM vs SM + EFT', fontsize=14)
    ax.set_xlabel(r'LLR')
    ax.set_ylabel(r'Frequency')
    l1=ax.legend(loc=1,fontsize=14)
    l2=ax.legend([r"$N_\mathrm{sm \: events} = %s$" "\n" "$N_\mathrm{eft \: events} = %s$" % (N_toy_events[0],N_toy_events[1]-N_toy_events[0])],loc=2,prop={'size':14},handlelength=0,handletextpad=0)
    ax.add_artist(l1)
    ax.set_xlabel('LLR',fontsize=14)
    ax.set_ylabel('Frequency',fontsize=14)
    plt.savefig(plot_dir + "SM{}_LLR_{}toy_events".format(anomaly_type, N_toy_events) + fig_specification + ".pdf")

    return LLRsm_histo, LLRsm_bins, LLReft_histo, LLReft_bins

# ================================== Some binning stuff ======================================================

# A check that area of pdf = 1:
sm_bin_width = sm_bins[1] - sm_bins[0]
eft_bin_width = eft_bins[1] - eft_bins[0]
print("Area of unscaled sm pdf =",sm_reference_pdf.sum()*sm_bin_width)
print("Area of unscaled eft pdf =",eft_reference_pdf.sum()*eft_bin_width)

mixed_bin_width = mixed_bins[1] - mixed_bins[0]

# =================================== Plot -2nln(lambda) for an individual toy ==================================
# I have removed this to keep the code concise but if we want to add it we can adapt it from an older version


# = Run the scipt to get LLR distributions, and calcualte seperation for a number of toy experiments ======================

def run_toys_luminosity(luminosity, prob_threshold, sm_cross_section, eft_cross_section, detector_efficiency):
    # Get total number of events - these will be used as means in the Poisson distributions
    mean_N_toy_sm_events = int(luminosity*detector_efficiency*sm_cross_section)
    mean_N_toy_mixed_events = int(luminosity*detector_efficiency*eft_cross_section) # N will be greater for mixed? Well this is the proper way of doing it - luminosity is the thing controlled, not number of events

    # Get n events for each toy as a number sampled from the poisson distribution with some mean
    # This list will be used for n events in both poisson factor and probs pdf factor
    N_toy_sm_events_list = []
    N_toy_mixed_events_list = []
    for toy in range(N_toys):
        N_toy_sm_events = np.random.poisson(mean_N_toy_sm_events)
        N_toy_mixed_events = np.random.poisson(mean_N_toy_mixed_events)
        N_toy_sm_events_list.append(N_toy_sm_events)
        N_toy_mixed_events_list.append(N_toy_mixed_events)
    #print(N_toy_sm_events_list)
    #print(N_toy_mixed_events_list)

    print("\n\n")
    print("Pcut:",prob_threshold)
    print("luminosity:",luminosity)
    print("N SM toys",mean_N_toy_sm_events)
    print("N mixed toys",mean_N_toy_mixed_events)

    # Make a cut on the pdf
    print("fraction of SM pdf before:",sm_reference_pdf.sum()*sm_bin_width)
    print("fraction of mixed pdf before cut:",mixed_reference_pdf.sum()*eft_bin_width)

    # Copy and cut on pdf and bins
    sm_reference_pdf_cut = np.stack(list(sm_reference_pdf))
    mixed_reference_pdf_cut = np.stack(list(mixed_reference_pdf))
    sm_bins_centered_cut = np.stack(list(sm_bins_centered))
    mixed_bins_centered_cut = np.stack(list(mixed_bins_centered))

    sm_reference_pdf_cut = np.delete(sm_reference_pdf_cut,np.where(sm_bins_centered < prob_threshold)[0])
    mixed_reference_pdf_cut = np.delete(mixed_reference_pdf_cut,np.where(mixed_bins_centered < prob_threshold)[0])
    sm_bins_centered_cut = np.delete(sm_bins_centered_cut,np.where(sm_bins_centered < prob_threshold)[0])
    mixed_bins_centered_cut = np.delete(mixed_bins_centered_cut,np.where(mixed_bins_centered < prob_threshold)[0])

    # Reduce number of events if cutting
    epsilon_sm = sm_reference_pdf_cut.sum()*sm_bin_width
    epsilon_mixed = mixed_reference_pdf_cut.sum()*mixed_bin_width
    print("Epsilons:",epsilon_sm, epsilon_mixed)

    mean_N_sm_after_cut = int(epsilon_sm*mean_N_toy_sm_events)
    mean_N_mixed_after_cut = int(epsilon_mixed*mean_N_toy_mixed_events)

    N_sm_after_cut_list = []
    N_mixed_after_cut_list = []
    for toy in range(N_toys):
        N_sm_after_cut = int(epsilon_sm*N_toy_sm_events_list[toy])
        N_mixed_after_cut = int(epsilon_mixed*N_toy_mixed_events_list[toy])
        N_sm_after_cut_list.append(N_sm_after_cut)
        N_mixed_after_cut_list.append(N_mixed_after_cut)

        #print("N SM before cut:", N_toy_sm_events_list[toy], "N SM after cut:", N_sm_after_cut, "fraction of SM pdf remaining after cut:",sm_reference_pdf_cut.sum()*sm_bin_width) # this will be wrong now, but it is just a print
        #print("N mixed before cut:", N_toy_mixed_events_list[toy], "N mixed after cut:", N_mixed_after_cut, "fraction of mixed pdf remaining after cut:",mixed_reference_pdf_cut.sum()*mixed_bin_width)# this will be wrong now, but it is just a print

    print("The sm bins that will be sampled from:",sm_bins_centered_cut)
    print("The mixed bins that will be sampled from:",mixed_bins_centered_cut)
    print("The sm pdfs that will be sampled from:",sm_reference_pdf_cut)
    print("The mixed pdfs that will be sampled from:",mixed_reference_pdf_cut)

    # Renorm pdfs
    sm_reference_pdf_cut = sm_reference_pdf_cut*(1.0/(sm_reference_pdf_cut.sum()*np.diff(sm_bins_centered_cut)[0]))
    mixed_reference_pdf_cut = mixed_reference_pdf_cut*(1.0/(mixed_reference_pdf_cut.sum()*np.diff(mixed_bins_centered_cut)[0]))
    print("PDF RENORMALISATION CHECK",sm_reference_pdf_cut.sum()*sm_bin_width)
    print("PDF RENORMALISATION CHECK",mixed_reference_pdf_cut.sum()*mixed_bin_width)

    # Plot PDFs after making a cut - this method is bad because matplotlib bar sucks for plotting
    plot_cut_pdfs = False
    if plot_cut_pdfs == True:
        fig, ax = plt.subplots(1,1, figsize = (8,8))
        #ax.hist(sm_reference_pdf_cut, bins = np.linspace(0, max_bin, nbins), label = 'SM', density = True, alpha = 0.5)
        #ax.hist(mixed_reference_pdf_cut, bins = np.linspace(0, max_bin, nbins), label = 'Mixed', density = True, alpha = 0.5)
        ax.bar(mixed_bins_centered_cut, mixed_reference_pdf_cut, width=np.diff(mixed_bins_centered_cut)[0], label = 'SM+EFT', alpha = 0.7)
        ax.bar(sm_bins_centered_cut, sm_reference_pdf_cut, width=np.diff(sm_bins_centered_cut)[0], label = 'SM', alpha = 0.7)
        ax.legend()
        ax.set_xlabel(r'$R$')
        ax.set_title(r"SM vs EFT $P_\mathrm{cut}(\mathrm{EFT}) = %s$" % prob_threshold)
        ax.set_xlim()
        plt.savefig(plot_dir + "pdfs_with_pcut" + str(prob_threshold) + 'Pcut' + fig_specification + ".pdf")

    # Sample
    cut_probs_pdf = False
    # If cutting on probs PDF
    if cut_probs_pdf == True:
        sm_sample_toy_log_likelihoodsm, sm_sample_toy_log_likelihoodeft = sample_ll_from_toys(sm_reference_pdf_cut,sm_bins_centered_cut,mixed_reference_pdf_cut, N_toys = N_toys, N_toy_events = N_sm_after_cut_list)
        eft_sample_toy_log_likelihoodeft, eft_sample_toy_log_likelihoodsm = sample_ll_from_toys(mixed_reference_pdf_cut,mixed_bins_centered_cut, sm_reference_pdf_cut, N_toys = N_toys, N_toy_events = N_mixed_after_cut_list)

    # If not cutting on probs PDF
    elif cut_probs_pdf != True:
        sm_sample_toy_log_likelihoodsm, sm_sample_toy_log_likelihoodeft = sample_ll_from_toys(sm_reference_pdf,sm_bins_centered,mixed_reference_pdf, N_toys = N_toys, N_toy_events = N_toy_sm_events_list)
        eft_sample_toy_log_likelihoodeft, eft_sample_toy_log_likelihoodsm = sample_ll_from_toys(mixed_reference_pdf,mixed_bins_centered, sm_reference_pdf, N_toys = N_toys, N_toy_events = N_toy_mixed_events_list)

    print("fraction of SM pdf remaining after cut:",sm_reference_pdf_cut.sum()*sm_bin_width)
    print("fraction of mixed pdf remaining after cut:",mixed_reference_pdf_cut.sum()*eft_bin_width)

    # Calculate Poisson factor
    poisson_events_from_probs_cut = True
    if poisson_events_from_probs_cut == True:
        n_sm_list = N_sm_after_cut_list
        n_mixed_list = N_mixed_after_cut_list
        mu_sm = mean_N_sm_after_cut
        mu_mixed = mean_N_mixed_after_cut
    elif poisson_events_from_probs_cut != True:
        n_sm_list = N_toy_sm_events_list
        n_mixed_list = N_toy_mixed_events_list
        mu_sm = mean_N_toy_sm_events
        mu_mixed = mean_N_toy_mixed_events

    LLR_sm_poisson_list = []
    LLR_mixed_poisson_list = []
    for toy in range(N_toys):
        try:
            LLR_sm_poisson = -2*(n_sm_list[toy]*log(mu_sm/mu_mixed) + (mu_mixed - mu_sm))
            LLR_mixed_poisson = -2*(n_mixed_list[toy]*log(mu_sm/mu_mixed) + (mu_mixed - mu_sm))
        except:
            print("Poisson except!")
            LLR_sm_poisson = 0
            LLR_mixed_poisson = 0
        #print("LLR sm Poisson factor:", LLR_sm_poisson)
        #print("LLR mixed Poisson factor:", LLR_mixed_poisson)
        LLR_sm_poisson_list.append(LLR_sm_poisson)
        LLR_mixed_poisson_list.append(LLR_mixed_poisson)

    # Calculate ratio
    LLRsm_list=[]
    LLReft_list=[]
    for i in range(len(sm_sample_toy_log_likelihoodsm)):
        LLRsm = LLR_sm_poisson_list[i] + sm_sample_toy_log_likelihoodsm[i]-sm_sample_toy_log_likelihoodeft[i]
        LLReft = LLR_mixed_poisson_list[i] + eft_sample_toy_log_likelihoodsm[i]-eft_sample_toy_log_likelihoodeft[i]

        # Poisson only
        #LLRsm = LLR_sm_poisson_list[i]
        #LLReft = LLR_mixed_poisson_list[i]

        #print("\n",LLR_sm_poisson_list[i], sm_sample_toy_log_likelihoodsm[i]-sm_sample_toy_log_likelihoodeft[i], LLRsm)
        #print(LLR_mixed_poisson_list[i], eft_sample_toy_log_likelihoodsm[i]-eft_sample_toy_log_likelihoodeft[i], LLReft)
        LLRsm_list.append(LLRsm)
        LLReft_list.append(LLReft)
    print("LLRs",np.average(LLR_sm_poisson_list), np.average(sm_sample_toy_log_likelihoodsm)-np.average(sm_sample_toy_log_likelihoodeft), "N,b,s",mu_mixed,mu_sm,mu_mixed-mu_sm)
    print("LLRs",np.average(LLR_mixed_poisson_list), np.average(eft_sample_toy_log_likelihoodsm)-np.average(eft_sample_toy_log_likelihoodeft), "N,b,s",mu_mixed,mu_sm,mu_mixed-mu_sm)

    # Plot
    LLRsm_histo, LLRsm_bins, LLReft_histo, LLReft_bins= plot_llr(LLRsm_list, LLReft_list, 'eft', N_toys = 10000, N_toy_events = (mean_N_toy_sm_events, mean_N_toy_mixed_events), prob_threshold=prob_threshold)

    # Calculate alpha and n standard deviations
    import math
    try:
        alpha = get_alpha(LLRsm_list, LLReft_list, LLRsm_histo, LLRsm_bins, LLReft_histo, LLReft_bins)
        alpha = 1.0 - alpha
        if alpha > 0.5: # Shouldn't be needed but will keep in case
            alpha = 1.0 - alpha
        if math.isnan(alpha):
            alpha = 0.5
        if mean_N_toy_sm_events == mean_N_toy_mixed_events:
            alpha = 0.5
    except:
        alpha = 0.5
    try:
        alpha_no_beta = get_alpha_no_beta(LLRsm_list, LLReft_list, LLRsm_histo, LLRsm_bins, LLReft_histo, LLReft_bins)
        alpha_no_beta = 1.0 - alpha_no_beta
        if alpha_no_beta > 0.5: # Shouldn't be needed but will keep in case
            alpha_no_beta = 1.0 - alpha
        if math.isnan(alpha_no_beta):
            alpha_no_beta = 0.5
        if mean_N_toy_sm_events == mean_N_toy_mixed_events:
            alpha_no_beta = 0.5
    except:
        alpha_no_beta = 0.5
    try:
        alpha_exact = get_alpha_exact(LLRsm_list, LLReft_list, LLRsm_histo, LLRsm_bins, LLReft_histo, LLReft_bins)
        if alpha_exact > 0.5: # Shouldn't be needed but will keep in case
            alpha_exact = 1.0 - alpha_exact
        if math.isnan(alpha_exact):
            alpha_exact = 0.5
        if mean_N_toy_sm_events == mean_N_toy_mixed_events:
            alpha_exact = 0.5
    except:
        alpha_exact = 0.5

    nstdevs = get_nstdevs(alpha)
    nstdevs_no_beta = get_nstdevs(alpha_no_beta)
    nstdevs_exact = get_nstdevs(alpha_exact)
    print("alpha:",alpha, "nstdevs:", nstdevs)
    print("alpha no beta:",alpha_no_beta, "nstdevs no beta:", nstdevs_no_beta)
    print("alpha exact", alpha_exact, "nstdevs exact:", nstdevs_exact)

    return alpha, nstdevs, alpha_no_beta, nstdevs_no_beta, alpha_exact, nstdevs_exact

# ========================== Z vs Neft ===========================================

# During development, we may set a cross section ratio instead of using the actual cross sections. So get the eft cross section here
#eft_cross_section = eft_to_sm_ratio*sm_cross_section

# Convert cross sections from pb to fb
#sm_cross_section = sm_cross_section*10**3 # Already done
#eft_cross_section = eft_cross_section*10**3

detector_efficiency = 1
N_toys = args.ntoys


prob_threshold = args.pcut
luminosity_arr = np.linspace(0.1,8.0,30)
nstdevs_list = []
nstdevs_no_beta_list = []
nstdevs_exact_list = []
for luminosity in luminosity_arr:
    alpha, nstdevs, alpha_no_beta, nstdevs_no_beta, alpha_exact, nstdevs_exact = run_toys_luminosity(luminosity, prob_threshold, sm_cross_section, eft_cross_section, detector_efficiency)
    nstdevs_list.append(nstdevs)
    nstdevs_no_beta_list.append(nstdevs_no_beta)
    nstdevs_exact_list.append(nstdevs_exact)


# Save the arrays so we can plot them later

nstdevs_arr = np.stack((nstdevs_list))
nstdevs_no_beta_arr = np.stack((nstdevs_no_beta_list))
nstdevs_exact_arr = np.stack((nstdevs_exact_list))
np.savetxt(array_dir + 'luminosityZvsNeft_arr' + extension + '.txt', luminosity_arr)
np.savetxt(array_dir + 'nstdevsZvsNeft_arr' + extension + '.txt', nstdevs_arr)
np.savetxt(array_dir + 'nstdevs_no_betaZvsNeft_arr' + extension + '.txt', nstdevs_no_beta_arr)
np.savetxt(array_dir + 'nstdevs_exactZvsNeft_arr' + extension + '.txt', nstdevs_exact_arr)

# Load them in again
luminosity_arr = np.loadtxt(array_dir + 'luminosityZvsNeft_arr' + extension + '.txt')
nstdevs_arr = np.loadtxt(array_dir + 'nstdevsZvsNeft_arr' + extension + '.txt')
nstdevs_no_beta_arr = np.loadtxt(array_dir + 'nstdevs_no_betaZvsNeft_arr' + extension + '.txt')
nstdevs_exact_arr = np.loadtxt(array_dir + 'nstdevs_exactZvsNeft_arr' + extension + '.txt')

plt.figure()
#N_toy_sm_events = int(luminosity*detector_efficiency*sm_cross_section)
N_toy_mixed_events = int(luminosity*detector_efficiency*eft_cross_section)
plt.plot(luminosity_arr, nstdevs_arr,label = r'Approx')
plt.plot(luminosity_arr, nstdevs_exact_arr,label = r'Exact')
plt.legend()
plt.xlabel(r'$L$')
plt.ylabel(r'Significance $Z$')

plt.figure()
#N_toy_sm_events = int(luminosity*detector_efficiency*sm_cross_section)
#N_toy_mixed_events = int(luminosity*detector_efficiency*eft_cross_section)
N_toy_sm_events_list = []
N_toy_eft_events_list = []
for luminosity in luminosity_arr:
    #N_toy_sm_events = int(luminosity*detector_efficiency*sm_cross_section)
    N_toy_eft_events = int(luminosity*detector_efficiency*eft_cross_section)
    #N_toy_sm_events_list.append(N_toy_sm_events)
    N_toy_eft_events_list.append(N_toy_eft_events)
plt.plot(N_toy_eft_events_list, nstdevs_arr,label = r'Approx $N_\mathrm{SM} = $, $N_\mathrm{EFT} = $')
plt.plot(N_toy_eft_events_list, nstdevs_exact_arr,label = r'Exact $N_\mathrm{SM} =s$, $N_\mathrm{EFT} = $')
plt.plot(N_toy_eft_events_list, nstdevs_no_beta_arr,label = r'No beta $N_\mathrm{SM} =s$, $N_\mathrm{EFT} = $')
plt.legend()
plt.xlabel(r'$N_{eft}$')
plt.ylabel(r'Significance $Z$')

# =========================== Z vs Pcut ===========================================
"""
luminosity_arr = np.linspace(5,5,1)
#prob_threshold_list = [0.2,0.4,0.6,0.8]
prob_threshold_arr = np.linspace(0,0.8,4)

plt.figure()
nstdevs_list_list = []
nstdevs_exact_list_list = []
for luminosity in luminosity_arr:
    alpha_list = []
    nstdevs_list = []
    alpha_exact_list = []
    nstdevs_exact_list = []
    for prob_threshold in prob_threshold_arr:
        alpha, nstdevs, alpha_exact, nstdevs_exact = run_toys_luminosity(luminosity, prob_threshold, sm_cross_section, eft_cross_section, detector_efficiency)
        alpha_list.append(alpha)
        nstdevs_list.append(nstdevs)
        alpha_exact_list.append(alpha_exact)
        nstdevs_exact_list.append(nstdevs_exact)
    nstdevs_list_list.append(nstdevs_list)
    nstdevs_exact_list_list.append(nstdevs_exact_list)

# Save the arrays so we can plot them later
extension = '5L_' + extension
nstdevs_arr = np.stack((nstdevs_list_list))
nstdevs_exact_arr = np.stack((nstdevs_exact_list_list))
np.savetxt(array_dir + 'testluminosityZvsPcut_arr' + extension + '.txt', luminosity_arr)
np.savetxt(array_dir + 'testprob_thresholdZvsPcut_arr' + extension + '.txt', prob_threshold_arr)
np.savetxt(array_dir + 'testnstdevsZvsPcut_arr' + extension + '.txt', nstdevs_arr)
np.savetxt(array_dir + 'testnstdevs_exactZvsPcut_arr' + extension + '.txt', nstdevs_exact_arr)

# Load them in again
luminosity_arr = np.loadtxt(array_dir + 'testluminosityZvsPcut_arr' + extension + '.txt')
prob_threshold_arr = np.loadtxt(array_dir + 'testprob_thresholdZvsPcut_arr' + extension + '.txt')
nstdevs_arr = np.loadtxt(array_dir + 'testnstdevsZvsPcut_arr' + extension + '.txt')
nstdevs_exact_arr = np.loadtxt(array_dir + 'testnstdevs_exactZvsPcut_arr' + extension + '.txt')

plt.figure()
if luminosity_arr.size > 1:
    for i,luminosity in enumerate(luminosity_arr):
        N_toy_sm_events = int(luminosity*detector_efficiency*sm_cross_section)
        N_toy_mixed_events = int(luminosity*detector_efficiency*eft_cross_section)
        plt.plot(prob_threshold_arr, nstdevs_arr[i],label = r'Approx $N_\mathrm{SM} = %s$, $N_\mathrm{EFT} = %s$' % (N_toy_sm_events, N_toy_sm_events))
        plt.plot(prob_threshold_arr, nstdevs_exact_arr[i],label = r'Exact $N_\mathrm{SM} = %s$, $N_\mathrm{EFT} = %s$' % (N_toy_sm_events, N_toy_sm_events))
        plt.legend()
        plt.xlabel(r'$P_{cut}$')
        plt.ylabel(r'Significance $Z$')
        #plt.ylim(0,10)
else:
    N_toy_sm_events = int(luminosity*detector_efficiency*sm_cross_section)
    N_toy_mixed_events = int(luminosity*detector_efficiency*eft_cross_section)
    plt.plot(prob_threshold_arr, nstdevs_arr,label = r'Approx $N_\mathrm{SM} = %s$, $N_\mathrm{EFT} = %s$' % (N_toy_sm_events, N_toy_sm_events))
    plt.plot(prob_threshold_arr, nstdevs_arr,label = r'Exact $N_\mathrm{SM} = %s$, $N_\mathrm{EFT} = %s$' % (N_toy_sm_events, N_toy_sm_events))
    plt.legend()
    plt.xlabel(r'$P_{cut}$')
    plt.ylabel(r'Significance $Z$')
    #plt.ylim(0,10)
"""

# Run for specific values only for LLR plotting purposes
#luminosity = 2.0
#prob_threshold = 0
#alpha, nstdevs, alpha_exact, nstdevs_exact = run_toys_luminosity(luminosity, prob_threshold, sm_cross_section, eft_cross_section, detector_efficiency)

#plt.show(block=False)
#plt.ion()
plt.show()
