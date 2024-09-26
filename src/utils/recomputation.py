import copy
import math
from typing import List, Tuple

import pandas as pd

import sorting_algorithms as sa
import utils.saves_handler as saves_handler


def recompute_trueskill(save: dict) -> Tuple[sa.TrueSkill, List[float]]:
    """
    Recomputes the TrueSkill algorithm based on the data in 'save' and returns the 
    sorting algorithm and appropriate measures.

    Args:
        save (dict): A dictionary containing the necessary information.

    Returns:
        Tuple[TrueSkill, List[float]]: A tuple containing the updated TrueSkill 
        object and a list of computed RMS errors.
    """
    csv = pd.read_csv(saves_handler.get_path_to_save(save) + '.csv')
    csv = csv[csv['type'] == 'Ranking']
    sort_alg = sa.TrueSkill(
        data=save['sort_alg'].data,
        comparison_size=save['sort_alg'].comparison_size,
        comparison_max=save['sort_alg'].comparison_max)
    rmses = []
    prev_ratings = copy.deepcopy(sort_alg.ratings)

    for i, i_df in csv.iterrows():
        res = i_df['result'].replace(
            "[", "").replace(
            "]", "").replace(
            "'", "").split(", ")

        diff_lvls = [
            sa.DiffLevel(
                abs([int(s) for s in dl if s.isdigit()][0]))
            for dl in i_df['diff_levels'].split(", ")]

        if i_df['undone']:
            pass
        else:
            sort_alg.inference(i_df['user'], res, diff_lvls)

            if i > 0:
                rmse = math.sqrt(
                    sum(
                        (prev_ratings[key].mu - sort_alg.ratings[key].mu) ** 2
                        for key in sort_alg.data) / sort_alg.n)
                rmses.append(rmse)

            prev_ratings = copy.deepcopy(sort_alg.ratings)

    return sort_alg, rmses


def recompute_ratings(save: dict) -> sa.RatingAlgorithm:
    """
    Recomputes the ratings based on the data in 'save' using the rating algorithm and 
    returns the updated rating algorithm.

    Args:
        save (dict): A dictionary containing the necessary information.

    Returns:
        RatingAlgorithm: The updated rating algorithm object.
    """
    csv = pd.read_csv(saves_handler.get_path_to_save(save) + '.csv')
    csv = csv[csv['type'] == 'Rating']
    sort_alg = sa.RatingAlgorithm(
        data=save['sort_alg'].data)

    for _, i_df in csv.iterrows():

        res = i_df['result'].replace(
            "(", "").replace(
            ")", "").replace(
            "'", "").split(", ")

        if i_df['undone']:
            pass
        else:
            sort_alg.inference(i_df['user'], res[0], int(res[1]))

    return sort_alg


def recompute_hybridtrueskill(save: dict) -> Tuple[sa.HybridTrueSkill,
                                                   List[float]]:
    """
    Recomputes the HybridTrueSkill algorithm based on the data in 'save' and returns 
    the HybridTrueSkill object and computed RMS errors.

    Args:
        save (dict): A dictionary containing the necessary information.

    Returns:
        Tuple[HybridTrueSkill, List[float]]: A tuple containing the updated 
        HybridTrueSkill object and a list of computed RMS errors.
    """
    csv = pd.read_csv(saves_handler.get_path_to_save(save) + '.csv')

    sort_alg = sa.HybridTrueSkill(
        data=save['sort_alg'].data,
        comparison_size=save['sort_alg'].comparison_size,
        comparison_max=save['sort_alg'].comparison_max)

    rmses = []
    prev_ratings = []

    for i, i_df in csv.iterrows():
        if i_df['type'] == 'Rating':

            rating_res = i_df['result'].replace(
                "(", "").replace(
                ")", "").replace(
                "'", "").split(", ")

            res = rating_res[0]
            assessment = int(rating_res[1])

        elif i_df['type'] == 'Ranking':

            res = i_df['result'].replace(
                "[", "").replace(
                "]", "").replace(
                "'", "").split(", ")

            assessment = [
                sa.DiffLevel(
                    abs([int(s) for s in dl if s.isdigit()][0]))
                for dl in i_df['diff_levels'].split(", ")]

        if i_df['undone']:
            pass
        else:

            sort_alg.inference(i_df['user'], res, assessment)

            if not sort_alg.is_rating:
                if not prev_ratings:
                    prev_ratings = copy.deepcopy(sort_alg.sort_alg.ratings)

                if i > len(sort_alg.data):
                    rmse = math.sqrt(
                        sum(
                            (prev_ratings[key].mu -
                             sort_alg.sort_alg.ratings[key].mu)
                            ** 2 for key in sort_alg.sort_alg.data) /
                        sort_alg.sort_alg.n)
                    rmses.append(rmse)

                prev_ratings = copy.deepcopy(sort_alg.sort_alg.ratings)

    return sort_alg, rmses
