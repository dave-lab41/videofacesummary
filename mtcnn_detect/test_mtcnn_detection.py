import cv2
from os.path import basename
from utils.get_test_images import get_test_images
from mtcnn_detect.run_mtcnn import identify_chips
from mtcnn_detect.detect_face import create_mtcnn
import timeit
import tensorflow as tf


def main(test_file, test_folder, test_type, use_gpu, gpu_memory_fraction, margin, min_size, threshold, scale_factor):

    # Get dictionary with ground truth for test images from test_file
    pic_to_faces = get_test_images(test_file, test_folder)

    # Establish MTCNN threshold to be the same for all three networks
    threshold = [threshold, threshold, threshold]

    with tf.Graph().as_default():
        # Load tensorflow session and mtcnn
        if use_gpu:
            gpu_options = tf.GPUOptions(
                per_process_gpu_memory_fraction=gpu_memory_fraction)
            sess = tf.Session(
                config=tf.ConfigProto(
                    gpu_options=gpu_options,
                    log_device_placement=False))
        else:
            sess = tf.Session()
        with sess.as_default():
            pnet, rnet, onet = create_mtcnn(sess, None)

            if test_type == 'facecount':
                detection_results = list()
                total_truth = sum(list(pic_to_faces.values()))
                exact_matches = 0

                # Run detections
                for item in pic_to_faces:
                    image = cv2.imread(item)
                    truth = pic_to_faces[item]
                    file = basename(item)
                    _, num_detections = identify_chips(image, frame_number=-1, margin=10, min_size=40,
                                                       threshold=threshold, scale_factor=0.709, reduceby=1, pnet=pnet,
                                                       rnet=rnet, onet=onet)
                    detection_results.append(num_detections)
                    if truth == num_detections:
                        star = '* Exact Match'
                        exact_matches +=1
                    else:
                        star = ''
                    print("File {0} - Detected {1} - Truth {2}  {3}".format(file, num_detections, truth, star))

                exact_match_percentage = '%.2f' % (float(exact_matches)/len(pic_to_faces))
                print("\nExact Matches {0} - Total Tests {1} - Percentage {2}".format(
                    exact_matches, len(pic_to_faces), exact_match_percentage))

                total_detections = sum(detection_results)
                print("Total Faces Detected {0} - Total True Faces {1}".format(total_detections, total_truth))

            elif test_type == 'duration':

                duration_results = list()
                # Run detections
                for item in pic_to_faces:
                    image = cv2.imread(item)
                    truth = pic_to_faces[item]
                    file = basename(item)
                    setup = "from mtcnn_detect.run_mtcnn import identify_chips"
                    t = timeit.Timer(stmt='''identify_chips(image, frame_number=-1, margin=10, min_size=40,
                        threshold=threshold, scale_factor=0.709,reduceby=1, pnet=pnet, rnet=rnet, onet=onet)''',
                        setup=setup, globals=locals())
                    durations = t.repeat(10, 1)
                    durations_avg = float(sum(durations)/len(durations))
                    duration_results.append(durations_avg)
                    width, height = image.shape[0:2]
                    print("File {0} ({1}x{2}) - Average Detection Duration {3}".format(file, height, width, '%.2f' % durations_avg))

                total_durations = sum(duration_results)
                final_duration_avg = '%.2f' % (float(total_durations)/len(duration_results))
                print("Overall Average Detection Duration {0}".format(final_duration_avg))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Test mtcnn face detection on dataset with hand-labeled counts of detected faces')

    # Optional args
    parser.add_argument(
        '--test_file',
        type=str,
        default="/prog/test_data/url_file_faces_hash.txt",
        help='Comma delimited file with urls and number of faces in image (manually labeled). (default = url_numfaces.txt')

    # Optional args
    parser.add_argument(
        '--test_images',
        type=str,
        default="/test_images",
        help='Folder to store test images retrieved from input_file. (default = /test_images')

    parser.add_argument(
        '--test_type',
        type=str,
        default="facecount",
        help="Type of test to run. Options are 'facecount' or 'duration' (default = facecount")

    parser.add_argument(
        '--use_gpu',
        type=bool,
        default=False,
        help='Use GPU, if available with nvidia-docker. Default = False.')

    parser.add_argument(
        '--gpu_memory_fraction',
        type=float,
        default=0.8,
        help='If use_gpu is True, percentage of GPU memory to use. Default = 0.8.')

    parser.add_argument(
        '--margin',
        type=int,
        default=10,
        help='Pixel padding around face within aligned chip. Default = 10.')

    parser.add_argument(
        '--min_size',
        type=int,
        default=40,
        help='Minimum pixel size of face to detect. Default = 40.')

    parser.add_argument(
        '--threshold',
        type=float,
        default=0.85,
        help='Probability threshold to included a proposed face detection. Default = 0.85.')

    parser.add_argument(
        '--scale_factor',
        type=float,
        default=0.709,
        help='Image scale factor used during MTCNN face detection. Default = 0.709.')

    args = parser.parse_args()

    print(
        "Test parameters set as: \n \
           Test input file = {0} \n \
           Test image folder = {1} \n \
           Test Type = {2} \n \
           Use GPU = {3} \n \
           GPU Memory Fraction = {4} \n \
           Margin = {5} \n \
           Min Size = {6} \n \
           Threshold = {7} \n \
           Scale Factor = {8} \n "
        .format(
            args.test_file,
            args.test_images,
            args.test_type,
            args.use_gpu,
            args.gpu_memory_fraction,
            args.margin,
            args.min_size,
            args.threshold,
            args.scale_factor))
    main(args.test_file, args.test_images, args.test_type, args.use_gpu, args.gpu_memory_fraction,
         args.margin, args.min_size, args.threshold, args.scale_factor)
    print("Finished test.")

