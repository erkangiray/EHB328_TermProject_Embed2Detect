# Created by Hansi at 3/16/2020
import logging
import os

from algo.cluster_change_calculation import calculate_cluster_change
from algo.utils.vocabulary_calculation import load_wordcounts, filter_vocabulary_by_frequency, preprocess_vocabulary
from algo.vocabulary_change_calculation import calculate_vocab_change
from project_config import model_type
from utils.file_utils import save_row, get_file_extension
from utils.word_embedding_util import load_model, get_vocab

logger = logging.getLogger(__name__)


class EventWindow:
    def __init__(self, time_window, average_diff, diff_ut_matrix, vocab):
        self.time_window = time_window
        self.average_diff = average_diff
        self.diff_ut_matrix = diff_ut_matrix
        self.vocab = vocab


def get_sorted_timeframes(model_folder_path: str) -> list:
    """
    Given the model folder, sort the model names within it in ascending order

    :param model_folder_path: folder path
        Path to folder which contains model files (files with '.model' extension).
    :return: list
        Sorted file name list
    """
    time_frames = []
    for root, dirs, files in os.walk(model_folder_path):
        for file in files:
            # only consider .model files
            if get_file_extension(file) == '.model':
                file_name = os.path.splitext(file)[0]
                time_frames.append(file_name)

    time_frames.sort()
    return time_frames


def get_event_windows(model_folder_path: str, stat_folder_path: str, alpha: float, beta: int = 0,
                      preprocess: object = None, workers: int = 1, similarity_type: str = 'dl',
                      aggregation_method: object = None, result_file: str = None) -> object:
    """
    Method to identify event occurred time windows

    parameters
    -----------
    :param model_folder_path: folder path
        Path to folder which contains word embedding models
    :param stat_folder_path: folder path
        Path to folder which contains stat details of data
    :param alpha: float
        Hyper-parameter alpha (threshold for overall change)
    :param beta: float, optional
        Hyper-parameter beta (threshold for word frequency)
    :param preprocess: None or list, optional
        None if no preprocessing required or a list of ordered preprocessing steps otherwise.
        Supported preprocessing steps are as follows.
        -'rm-punct': remove punctuation marks
        -'rm-stop_words': remove stop words
    :param workers: int, optional
        Number of worker threads to use with event window identification.
    :param similarity_type: {'dl', 'cos'}, optional
        Similarity type to use with similarity matrix generation.
    :param aggregation_method: None or {'avg', 'max'}, optional
        None returns only the cluster change with no aggregation as the final value.
        Given a method, it will be applied to cluster change and vocabulary change measures to generate the final value.
    :param result_file: .tsv file path, optional
        File path to save time window and overall change details.
    :return: list
        List of EventWindows
    """

    time_frames = get_sorted_timeframes(model_folder_path)
    logger.info(f'length of time frames {len(time_frames)}')

    event_windows = []

    for index in range(0, len(time_frames)):
        if index < (len(time_frames) - 1):
            t1 = time_frames[index]
            t2 = time_frames[index + 1]
            info_label = t1 + '-' + t2
            logger.info(f'processing {info_label}')

            # load word embedding models
            model1 = load_model(os.path.join(model_folder_path, t1 + '.model'), model_type)
            model2 = load_model(os.path.join(model_folder_path, t2 + '.model'), model_type)
            # load stats
            word_counts1 = load_wordcounts(os.path.join(stat_folder_path, t1 + '.tsv'))
            word_counts2 = load_wordcounts(os.path.join(stat_folder_path, t2 + '.tsv'))
            # get vocabularies
            vocab1 = get_vocab(model1)
            vocab2 = get_vocab(model2)

            # get common vocabulary
            common_vocab = vocab2
            if preprocess:
                common_vocab = preprocess_vocabulary(common_vocab, preprocess)
            if beta > 0:
                common_vocab = filter_vocabulary_by_frequency(common_vocab, word_counts2, beta)
            common_vocab.sort()

            # calculate cluster change
            cluster_change, diff_ut_matrix = calculate_cluster_change(model1, model2, common_vocab, workers=workers,
                                                                      similarity_type=similarity_type)
            if not aggregation_method:
                average_diff = cluster_change
            else:
                vocab_change = calculate_vocab_change(vocab1, vocab2, word_counts1, word_counts2,
                                                      frequency_threshold=beta,
                                                      preprocess=preprocess)
                if 'max' == aggregation_method:
                    average_diff = max(cluster_change, vocab_change)
                elif 'avg' == aggregation_method:
                    average_diff = (cluster_change + vocab_change) / 2
                else:
                    raise KeyError('Unknown aggregation method found')

            if average_diff > alpha:
                event_windows.append(EventWindow(t2, average_diff, diff_ut_matrix, common_vocab))
                if result_file:
                    save_row([t2, average_diff], result_file)
    return event_windows