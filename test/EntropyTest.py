import sys
sys.path.append('../')
from goldfish.entropy import EntropyWatermarker
from goldfish.message import create_dummy_message
import uuid
import os, binascii, random, time

from PIL import Image, ImageMath
#from skimage import data

from argparse import ArgumentParser
from StringIO import StringIO

imagetypes = ('jpeg', 'png', 'bmp')

parser = ArgumentParser()
parser.add_argument('image', help='Path to the image to test with')
parser.add_argument('-n', '--n-rounds', type=int, default=1,
        help='Number of rounds to perform')
parser.add_argument('-t', '--type', choices=imagetypes, default=imagetypes[0],
        help='Filetype to save during test')
parser.add_argument('-q', '--quality', type=int, default=95,
        help='Compression quality watermark should resist')
parser.add_argument('-e', '--entropy-threshold', type=int, default=4000,
        help='Block entropy threshold')
parser.add_argument('-b', '--bits-per-block', type=int, default=16,
        help='Bits per block to embed')
parser.add_argument('-c', '--channel', default='luma',
        help='Channel to embed in (luma is best)')
parser.add_argument('-m', '--message', type=str,
        help='Specify a message to embed')
parser.add_argument('--debug', action='store_true',
        help='Enable debug messages')
parser.add_argument('--super-debug', action='store_true',
        help='Enable debug messages and show embedding')
parser.add_argument('--quiet', action='store_true',
        help='Disable all output')
parser.add_argument('-d', '--data-size', type=int, default=32,
        help='How many bytes of watermark data to embed/extract')
parser.add_argument('--direct', action='store_true',
        help='Directly decode the watermarked image to test insertions/deletions')
parser.add_argument('--stream', action='store_true',
        help='Use this for running in make to avoid saving to disk')
parser.add_argument('--time', action='store_true',
        help='Time the embedding process')
args = parser.parse_args()

n_rounds = args.n_rounds
successes = 0
# yes this is stupid
hex_digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
times = []
ext_times = []
start = 0

print_len = len(str(n_rounds))
if args.super_debug:
    args.debug = True

for i in range(n_rounds):
    if not args.quiet:
        print '{num:{w}}/{t}'.format(num=i+1, w=print_len, t=n_rounds)
    infile = args.image
    outfile = '.'.join(infile.split('.')[:-1])+'-altered.' + args.type
    #outfile = StringIO()

    if args.message == None:
        message = ''.join([random.choice(hex_digits) for _ in range(args.data_size)])
    else:
        message = args.message
        if args.data_size != len(message):
            print 'Specified message and data size are mismatched'
            sys.exit(1)

    if args.debug and not args.quiet:
        print 'Length of message (bytes) =', len(message)
        print 'Length of message (bits) =', len(message)*8
    #message = create_dummy_message()[:args.data_size] #uuid.uuid4().hex
    resilience = args.quality
    if args.quality > 75 or args.type != 'jpeg':
        resilience = 75
    wm = EntropyWatermarker(quality=resilience,
            bits=args.bits_per_block,
            threshold=args.entropy_threshold,
            chan=args.channel,
            debug=args.debug,
            show_embed=args.super_debug)

    #print 'Embedding message \"'+message+'\" into image'

    if args.time:
        start = time.time()
    im_out = wm.embed(infile, message)
    end = time.time()
    if args.time:
        times.append(end - start)

    if args.super_debug:
        im = Image.open(infile)
        im.show()
        im_out.show()
        sys.exit()


    if not args.direct:
        if args.debug:
            print 'Saving to', outfile
        im_out.save(outfile, format=args.type, quality=95)#args.quality)
        im_out = Image.open(outfile)
    if args.time:
        start = time.time()
    retrieved = wm.extract(im_out, message_length=args.data_size*8)
    end = time.time()
    if args.time:
        ext_times.append(end - start)

    if args.debug:
        print message
        print retrieved

    if message != retrieved:
        if n_rounds == 1 and not args.quiet:
            print
            print 'Failure!'
            with open('orig', 'w') as f:
                f.write(message)
            with open('decoded', 'w') as f:
                f.write(retrieved)
    else:
        if n_rounds == 1 and not args.quiet:
            print 'Success!'
        successes += 1

if not args.quiet:
    print successes, 'successful extractions out of', n_rounds
if args.time:
    print sum(times)/len(times), 's average embed time'
    print sum(ext_times)/len(ext_times), 's average extract time'

sys.exit(successes)

'''
print 'Getting the diff'
im_in = Image.open(infile)
in_bands = im_in.split()
out_bands = im_out.split()
diffs = [ImageMath.eval("convert(b-a, 'L')", a=in_bands[i], b=out_bands[i])
        for i in range(len(in_bands))]
diff = Image.merge('RGB', diffs)
diff.save('diff.png')
'''
