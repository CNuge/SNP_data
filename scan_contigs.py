import os
import pandas as pd
from pandas import DataFrame

def read_vcf_locations(vcf_name):
	""" read in the .vcf, get the contig and position columns
		and return a list of tuples"""
	storage_location =[]
	with open(vcf_name) as file:
		for line in file:
			if line[0] == '#':
				continue
			else:
				data=line.split('\t')
				storage_location.append((data[0], data[1]))
	return storage_location

def contig_file_reader(contig_file):
	""" read in the contig file of style:
		Contig	Size	Size_rank
		of each contig and return in a dataframe """
	in_file = pd.read_table(contig_file, sep='\t')
	return in_file

def snp_pos_dictonary(contig_list, snp_df):
	location_dict = {}
	for i in set(list(contig_list['Contig'])):
		location_dict[i] = []
	for snp in snp_df.iterrows():
		if snp[1]['Pos'] == '-':
			continue
		else:
			location_dict[snp[1]['Contig']].append(int(snp[1]['Pos']))
	return location_dict

def find_gaps(dictonary_of_snps, contig_dat):
	""" compare the locations and find the regions with big gaps
		also looks at the last snp -> end of contig distance """
	gaps_list = []
	""" tuples in form (contig, left_snp, right_snp)"""
	for contig in dictonary_of_snps.keys():
		end_pos = int(contig_dat[contig_dat['Contig'] == contig]['Size'])
		position_list = sorted(dictonary_of_snps[contig])
		""" check the beginning position relative to 0, and the last position
			relative to the length of the contig. then step through all the
			intermediate locations """
		if position_list[0] > 50000:
			""" add front gaps to the list"""
			gaps_list.append((contig, 0, position_list[0]))
		if (position_list[-1] + 50000) < end_pos:
			"""add trailing gaps to the list """
			gaps_list.append((contig, position_list[-1], end_pos))
		
		pos_1 = 0
		pos_2 = 1
		while pos_2 < len(position_list):
			if (position_list[pos_1] + 50000) > position_list[pos_2]:
				continue
			else:
				""" there is a 50000 or more bp gap here """
				gaps_list.append((contig, position_list[pos_1], position_list[pos_2]))
			pos_1 += 1
			pos_2 += 1
	return gaps_list







if __name__ == '__main__':

	#list all the .vcf in the directory

	vcf_files = [x for x in os.listdir() if x[-3:] == 'vcf']

	#read them in, storing the contig and positions
	snp_tuples = []
	for file in vcf_files:
		snps_in_vcf = read_vcf_locations(file)
		snp_tuples.extend(snps_in_vcf)

	#make a dataframe for comparison purposes
	snp_df = DataFrame(snp_tuples,columns=['Contig', 'Pos'])

	#read in the list of contigs.
	contig_dat = contig_file_reader('contigs_ranked_by_size.txt')

	#get the contigs that have no SNPs on them
	unreped_contigs = contig_dat[~contig_dat['Contig'].isin(snp_df['Contig'])]

	#print non represented contigs to a file
	unreped_contigs.to_csv('contigs_with_no_snps.tsv', sep='\t', index=False)


	#get contigs with representitives 
	reped_contigs = contig_dat[contig_dat['Contig'].isin(snp_df['Contig'])]

	#build the dictonary of snp locations
	contig_hit_dict = snp_pos_dictonary(reped_contigs, snp_df)

	gaps_in_contigs = find_gaps(contig_hit_dict, reped_contigs)

