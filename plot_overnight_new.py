import os, sys
import matplotlib as mpl
if os.environ.get('DISPLAY','') == '':
	print('no display found. Using non-interactive Agg backend')
	mpl.use('Agg')

from matplotlib import pyplot as plt
import numpy as np
import scio, datetime, time
import SNAPfiletools as sft
import argparse


#============================================================

def get_avg(arr,block=50):
    iters=arr.shape[0]//block
    leftover=arr.shape[0]%block
    print(arr.shape, iters, leftover)
    if(leftover>0.5*block):
        result=np.zeros((iters+1,arr.shape[1]))
    else:
        result=np.zeros((iters,arr.shape[1]))
        
    for i in range(0,iters):
        result[i,:] = np.mean(arr[i*block:(i+1)*block,:],axis=0)
    
    if(leftover>0.5*block):
        result[-1,:] = np.mean(arr[iters*block:,:],axis=0)
        
    return result

if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	# parser.set_usage('python plot_overnight_data.py <start time as YYYYMMDD_HHMMSS> <stop time as YYYYMMDD_HHMMSS> [options]')
	# parser.set_description(__doc__)
	parser.add_argument('data_dir', type=str,help='Direct data directory')
	parser.add_argument("time_start", type=str, help="Start time YYYYMMDD_HHMMSS")
	parser.add_argument("time_stop", type=str, help="Stop time YYYYMMDD_HHMMSS")
	parser.add_argument('-o', '--outdir', dest='outdir',type=str, default='/project/s/sievers/mohanagr/plots',
			  help='Output plot directory')
	
	parser .add_argument('-n', '--length', dest='readlen', type=int, default=1000, help='length of integration time in seconds')
	parser.add_argument("-l", "--logplot", dest='logplot',action="store_true", help="Plot in logscale")
	parser.add_argument("-a", "--avglen",dest="blocksize",default=False,type=int,help="number of chunks (rows) of direct spectra to average over. One chunk is roughly 6 seconds.")
	args = parser.parse_args()



	data_dir = args.data_dir
	plot_dir = args.outdir
	#print(data_dir)
	
	ctime_start = sft.timestamp2ctime(args.time_start)
	ctime_stop = sft.timestamp2ctime(args.time_stop)
	print('In cTime from: ' + str(ctime_start) + ' to ' + str(ctime_stop))

	#all the dirs between the timestamps. read all, append, average over chunk length
	data_subdirs = sft.time2fnames(ctime_start, ctime_stop, data_dir)
	new_dirs = [d+'/pol00.scio.bz2' for d in data_subdirs]
	datpol00 = scio.read_files(new_dirs)
	new_dirs = [d+'/pol11.scio.bz2' for d in data_subdirs]
	datpol11 = scio.read_files(new_dirs)
	new_dirs = [d+'/pol01r.scio.bz2' for d in data_subdirs]
	datpol01r = scio.read_files(new_dirs)
	new_dirs = [d+'/pol01i.scio.bz2' for d in data_subdirs]
	datpol01i = scio.read_files(new_dirs)

	t1=time.time()
	pol00=datpol00[0]
	for d in datpol00[1:]:
		pol00=np.append(pol00,d,axis=0)
	

	pol11=datpol11[0]
	for d in datpol11[1:]:
		pol11=np.append(pol11,d,axis=0)

	pol01r=datpol01r[0]
	for d in datpol01r[1:]:
		pol01r=np.append(pol01r,d,axis=0)

	pol01i=datpol01i[0]
	for d in datpol01i[1:]:
		pol01i=np.append(pol01i,d,axis=0)

	t2=time.time()
	print('time taken for append',t2-t1)
	print(pol00.shape,pol11.shape,pol01r.shape,pol01i.shape)
	# Remove starting data chunk if it's bad :(
	pol00 = pol00[1:,:]
	pol11 = pol11[1:,:]
	pol01r = pol01r[1:,:]
	pol01i = pol01i[1:,:]
	

	if(args.blocksize):
		pol00=get_avg(pol00,block=args.blocksize)
		pol11=get_avg(pol11,block=args.blocksize)
		pol01r=get_avg(pol01r,block=args.blocksize)
		pol01i=get_avg(pol01i,block=args.blocksize)

	pol01 = pol01r + 1J*pol01i

	freq = np.linspace(0, 125, np.shape(pol00)[1])

	pol00_med = np.median(pol00, axis=0)
	pol11_med = np.median(pol11, axis=0)
	pol00_mean = np.mean(pol00, axis=0)
	pol11_mean = np.mean(pol11, axis=0)
	pol00_max = np.max(pol00, axis = 0)
	pol11_max = np.max(pol11, axis = 0)
	pol00_min = np.min(pol00, axis = 0)
	pol11_min = np.min(pol11, axis = 0)
	med = np.median(pol00)
	pmax = np.max(pol00)

	xx=np.ravel(pol00).copy()
	u=np.percentile(xx,99)
	b=np.percentile(xx,1)
	xx_clean=xx[(xx<=u)&(xx>=b)] # remove some outliers for better plotting
	stddev = np.std(xx_clean)
	vmin= max(med - 2*stddev,10**7)
	vmax = med + 2*stddev
	axrange = [0, 125, 0, pmax]
	if args.logplot is True:
		pol00 = np.log10(pol00)
		pol11 = np.log10(pol11)
		pol00_mean = np.log10(pol00_mean)
		pol11_mean = np.log10(pol11_mean)
		pol00_med = np.log10(pol00_med)
		pol11_med = np.log10(pol11_med)
		pol00_max = np.log10(pol00_max)
		pol11_max = np.log10(pol11_max)
		pol00_min = np.log10(pol00_min)
		pol11_min = np.log10(pol11_min)
		pmax = np.log10(pmax)
		vmin = np.log10(vmin)
		vmax = np.log10(vmax)
		
		axrange = [0, 125, 6.5, pmax]

	myext = np.array([0,125,pol00.shape[0],0])
		
	plt.figure(figsize=(18,10), dpi=200)

	plt.subplot(2,3,1)

	print(pol00.shape)
	plt.imshow(pol00, vmin=vmin, vmax=vmax, aspect='auto', extent=myext)
	plt.title('pol00')
	cb00 = plt.colorbar()
	# cb00.ax.plot([0, 1], [7.0]*2, 'w')

	plt.subplot(2,3,4)
	plt.imshow(pol11, vmin=vmin, vmax=vmax, aspect='auto', extent=myext)
	plt.title('pol11')
	plt.colorbar()

	plt.subplot(2,3,2)
	plt.title('Basic stats for frequency bins')
	plt.plot(freq, pol00_max, 'r-', label='Max')
	plt.plot(freq, pol00_min, 'b-', label='Min')
	plt.plot(freq, pol00_mean, 'k-', label='Mean')
	plt.plot(freq, pol00_med, color='#666666', linestyle='-', label='Median')
	plt.xlabel('Frequency (MHz)')
	plt.ylabel('pol00')
	plt.axis(axrange)

	plt.subplot(2,3,5)
	plt.plot(freq, pol11_max, 'r-', label='Max')
	plt.plot(freq, pol11_min, 'b-', label='Min')
	plt.plot(freq, pol11_mean, 'k-', label='Mean')
	plt.plot(freq, pol11_med, color='#666666', linestyle='-', label='Median')
	plt.xlabel('Frequency (MHz)')
	plt.ylabel('pol11')
	plt.axis(axrange)
	plt.legend(loc='lower right', fontsize='small')

	plt.subplot(2,3,3)
	plt.imshow(np.log10(np.abs(pol01)), vmin=3,vmax=8,aspect='auto', extent=myext)
	plt.title('pol01 magnitude')
	plt.colorbar()

	plt.subplot(2,3,6)
	plt.imshow(np.angle(pol01), vmin=-np.pi, vmax=np.pi, aspect='auto', extent=myext, cmap='RdBu')
	plt.title('pol01 phase')
	plt.colorbar()

	plt.suptitle('Averaged over {} chunks'.format(args.blocksize))

	outfile = os.path.join(args.outdir,'output'+ '_' + str(ctime_start) + '_' + str(ctime_stop) + '.png')
	plt.savefig(outfile)
	print('Wrote ' + outfile)