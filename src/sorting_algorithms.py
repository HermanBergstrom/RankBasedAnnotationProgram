import copy
import random
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any, Dict, List, Optional, Union
from tqdm import tqdm

import numpy as np
from trueskill import Rating, rate_1vs1


class DiffLevel(IntEnum):
    none = 0
    normal = 1
    major = 2


class SortingAlgorithm (ABC):
    """Abstract base class for sorting algorithms."""

    @abstractmethod
    def get_comparison(self, user_id: str) -> List[str]:
        """
        Fetches a new comparison based on the state of the sorting algorithm.

        Args:
            user_id: the ID of the user that is to perform the comparison.
        Returns:
            a list containing the keys of the elements that are to be compared.
        """

        pass

    @abstractmethod
    def inference(
            self, user_id: str, keys: List[str],
            diff_lvls: List[DiffLevel]):
        """
        Updates the algorithms estimated ordering based on the 
        results of a comparison.

        Args:
            user_id: the ID of the user that has performed the comparison.
            keys: an ordered list of the keys which the user compared.
            diff_lvls: a list containing the DiffLevels of adjacent 
            elements in keys.
        """
        pass

    @abstractmethod
    def get_result(self):
        """
        Returns the current result of the sorting algorithm.

        Returns:
            the result of the sorting algorithm.
        """
        pass

    @abstractmethod
    def is_finished(self):
        """
        Checks if the sorting algorithm has finished sorting.

        Returns:
            a boolean value indicating whether the sorting algorithm 
            has finished.
        """
        pass

    @abstractmethod
    def comparison_is_available(self, user_id):
        """
        Checks if a comparison is available for the given user.

        Args:
            user_id: the ID of the user that is to perform the comparison.

        Returns:
            a boolean value indicating whether a comparison is available.
        """
        pass

    @abstractmethod
    def get_comparison_count(self):
        """
        Returns the total number of comparisons performed by the 
        sorting algorithm.

        Returns:
            the number of comparisons performed.
        """
        pass

    @abstractmethod
    def get_comparison_max(self):
        """
        Returns the maximum number of comparisons allowed 
        by the sorting algorithm.

        Returns:
            the maximum number of comparisons allowed.
        """
        pass


class MergeSort(SortingAlgorithm):
    """Implementation of the Merge Sort algorithm"""

    def __init__(self, data: List[Union[int, float, str]]):
        """
        Initialize the MergeSort object.

        Args:
            data: The list of values to be sorted.
        """

        self.data = data
        self.comparison_size = 2
        self.current_layer = [[value] for value in data]
        self.next_sorted = [[]]
        self.comp_count = 0

    def get_comparison(self, user_id: str) -> List[Union[int, float, str]]:
        """
        Get the next comparison pair.

        Args:
            user_id: The ID of the user making the comparison.

        Returns:
            A list of two elements representing the next comparison pair.
        """
        return [self.current_layer[0][0], self.current_layer[1][0]]

    def inference(
            self, user_id: str, keys: List[Union[int, float, str]],
            diff_lvls: List[object]):
        """
        Perform the inference step based on the user's choices.

        Args:
            user_id: The ID of the user.
            keys: The keys of the items compared by the user.
            diff_lvls: The difference levels asessed by the user.
        """
        if self.current_layer[0][0] == keys[0]:
            smallest_i = 0
        else:
            smallest_i = 1

        smallest = self.current_layer[smallest_i].pop(0)

        if diff_lvls[0].value == 0:
            equally_smallest = self.current_layer[1 - smallest_i].pop(0)

        if not self.current_layer[0] or not self.current_layer[1]:
            if diff_lvls[0].value == 0:
                layer = [smallest] + [equally_smallest] + \
                    self.current_layer.pop(0) + self.current_layer.pop(0)
            else:
                layer = [smallest] + \
                    self.current_layer.pop(0) + self.current_layer.pop(0)
            self.next_sorted[-1] += layer

            if len(self.current_layer) > 1:
                self.next_sorted.append([])
            else:
                if len(self.current_layer) == 1:
                    # add the remaining sublist to the next sorted layer
                    self.next_sorted += [self.current_layer.pop(0)]
                # update the current layer to the next sorted layer
                self.current_layer = self.next_sorted
                self.next_sorted = [[]]  # reset the next sorted layer

        else:
            # if neither of the two sublists in the current layer are empty,
            # add the smallest element to the current nested
            # list of the next sorted layer
            self.next_sorted[-1].append(smallest)
            if diff_lvls[0].value == 0:
                self.next_sorted[-1].append(equally_smallest)

        self.comp_count += 1

    def get_result(self) -> Optional[List[Union[int, float, str]]]:
        """
        Get the sorted result if the sorting process is finished.

        Returns:
            The sorted result as a list of values, or 
            None if the sorting is not finished.
        """

        if self.is_finished():
            # return the first and only sublist of the current layer if the
            return self.current_layer[0]

    def is_finished(self) -> bool:
        """
        Check if the sorting process is finished.

        Returns:
            True if the sorting process is finished, False otherwise.
        """
        return len(self.current_layer[0]) == len(self.data)

    def comparison_is_available(self, user_id: str) -> bool:
        """
        Check if there are more comparisons available for the user.

        Args:
            user_id: The ID of the user.

        Returns:
            True if there are more comparisons available, False otherwise.
        """
        return not self.is_finished()

    def get_comparison_count(self) -> int:
        """
        Get the number of comparisons made so far.

        Returns:
            The number of comparisons made.
        """
        return self.comp_count

    def get_comparison_max(self) -> int:
        """
        Get the maximum number of comparisons needed for the sorting process.

        Returns:
            The maximum number of comparisons needed.
        """
        n = len(self.data)
        return int(n * np.log(n))


class TrueSkill (SortingAlgorithm):
    """Implementation of the TrueSkill algorithm"""

    def __init__(
            self, data: List[Union[int, float, str]],
            comparison_size: int = 2, comparison_max: Optional[int] = None,
            initial_mus: Optional[Dict[Union[int, float, str],
                                       float]] = None,
            random_comparisons: bool = False, same_comp_amount=False, initial_std=None):
        """
        Initialize the TrueSkill object.

        Args:
            data: The list of values to be sorted.
            comparison_size (int): The number of items to compare in 
                                   each comparison.
            comparison_max (int): The maximum number of comparisons allowed.
            initial_mus: A dictionary containing the initial mean ratings 
                         for each value.
            random_comparisons: A flag indicating whether to perform random 
                                comparisons.
        """
        self.n = len(data)
        self.data = list(data)
        self.random_comparisons = random_comparisons
        self.same_comp_amount = same_comp_amount

        if comparison_max is None:
            self.comparison_max = self.n * 6
        else:
            self.comparison_max = comparison_max

        if initial_mus:
            if initial_std is not None:
                self.ratings = {
                    k: Rating(initial_mus[k], initial_std) for k in data}
            else:
                self.ratings = {
                    k: Rating(initial_mus[k]) for k in data}

            self.overlap_matrix = np.zeros((self.n, self.n))
            print("constructing overlap matrix")
            for i in tqdm(range(self.n)):
                for j in range(i + 1, self.n):
                    overlap = self.intervals_overlap(self.data[i],
                                                     self.data[j])
                    self.overlap_matrix[i, j] = overlap
                    self.overlap_matrix[j, i] = overlap
        else:
            self.ratings = {k: Rating() for k in data}

            self.overlap_matrix = np.full(
                (self.n, self.n),
                self.intervals_overlap(self.data[0],
                                       self.data[1]))

        np.fill_diagonal(self.overlap_matrix, -np.inf)

        if self.same_comp_amount:
            self.comp_tracker = np.zeros((self.n))

        self.comparison_size = comparison_size
        self.comp_count = 0

        self.user_comparisons = {}

    def intervals_overlap(
            self, key1: Union[int, float, str],
            key2: Union[int, float, str]) -> float:
        """
        Calculate the overlap between the intervals of two keys.

        Args:
            key1: The first key.
            key2: The second key.

        Returns:
            The overlap value between the intervals.
        """
        std = 3

        r1_low = self.ratings[key1].mu - std * self.ratings[key1].sigma
        r1_high = self.ratings[key1].mu + std * self.ratings[key1].sigma

        r2_low = self.ratings[key2].mu - std * self.ratings[key2].sigma
        r2_high = self.ratings[key2].mu + std * self.ratings[key2].sigma

        common_gap = min(r1_high, r2_high) - max(r1_low, r2_low)
        overall_gap = (max(r1_high, r2_high) - min(r1_low, r2_low))
        largest_span = max(r1_high-r1_low, r2_high-r2_low)

        return common_gap / overall_gap * largest_span

    def update_overlap_matrix(self, key: Union[int, float, str]):
        """
        Update the overlap matrix with the overlap values for a specific key.

        Args:
            key: The key to update the overlap matrix.
        """
        key_i = self.data.index(key)

        for i in range(self.n):
            if i != key_i:
                overlap = self.intervals_overlap(key, self.data[i])
                self.overlap_matrix[i][key_i] = overlap
                self.overlap_matrix[key_i][i] = overlap

    def get_comparison(self, user_id: str) -> List[Union[int, float, str]]:
        """
        Get the next comparison pair for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            A list containing the keys of the items to be compared.
        """
        max_sum = 0
        comparisons = []

        if user_id not in self.user_comparisons:
            self.user_comparisons[user_id] = np.ones(self.overlap_matrix.shape)

        if self.random_comparisons and self.comparison_size == 2:
            comparisons = random.sample(range(self.n), 2)
        else:

            masked_overlap_matrix = np.multiply(
                self.overlap_matrix, self.user_comparisons[user_id])

            if self.same_comp_amount and self.comparison_size == 2:
                arg_sorted_comps = np.argsort(self.comp_tracker)
                i = arg_sorted_comps[0]

                max_index = np.argmax(
                    masked_overlap_matrix[i])

                if i == max_index:
                    max_index = np.argpartition(masked_overlap_matrix[i], 2)[1]

                comparisons = [i, max_index]
            else:
                for i in range(self.n):
                    if self.comparison_size == 2:

                        max_index = np.argmax(masked_overlap_matrix[i])

                        if masked_overlap_matrix[i][max_index] > max_sum:

                            max_sum = masked_overlap_matrix[i][max_index]
                            comparisons = [i, max_index]

                    else:
                        indices = np.argpartition(
                            self.overlap_matrix[i], -self.comparison_size+1)[
                                -self.comparison_size+1:]
                        indices = [
                            ind for ind in indices
                            if self.overlap_matrix[i][ind] > 0]

                        sum_i = sum(self.overlap_matrix[i][indices])
                        if max_sum < sum_i:
                            max_sum = sum_i
                            comparisons = [i] + list(indices)

        keys_output = [list(self.ratings.keys())[c] for c in comparisons]

        return keys_output

    def inference(
            self, user_id: str, keys: List[Union[int, float, str]],
            diff_lvls: List[object]):
        """
        Perform the inference step based on the user's choices.

        Args:
            user_id: The ID of the user.
            keys: The keys of the items compared by the user.
            diff_lvls: The difference levels asessed by the user.
        """

        to_update = []

        for i in range(len(keys)):
            j = i + 1
            while j < len(keys):
                update = max([diff_lvl.value for diff_lvl in diff_lvls][i:j])

                if update == 0:
                    to_update.append(([i, j], True))

                else:
                    to_update.append(([i, j], False))
                    if update == 2:
                        to_update.append(([i, j], False))
                j += 1

        random.Random(6).shuffle(to_update)

        if user_id not in self.user_comparisons:
            self.user_comparisons[user_id] = np.ones(self.overlap_matrix.shape)

        for ([i, j], is_draw) in to_update:
            if is_draw:
                self.ratings[keys[j]], self.ratings[keys[i]] = rate_1vs1(
                    self.ratings[keys[j]], self.ratings[keys[i]], drawn=True)
            else:
                self.ratings[keys[j]], self.ratings[keys[i]] = rate_1vs1(
                    self.ratings[keys[j]], self.ratings[keys[i]])

            key_i = self.data.index(keys[i])
            key_j = self.data.index(keys[j])

            if self.same_comp_amount:
                self.comp_tracker[key_i] += 1
                self.comp_tracker[key_j] += 1

            self.user_comparisons[user_id][key_i, key_j] = 0
            self.user_comparisons[user_id][key_j, key_i] = 0

        for k in keys:
            self.update_overlap_matrix(k)

        self.comp_count += 1

    def get_result(self) -> List[Union[int, float, str]]:
        """
        Get the sorted result.

        Returns:
            A list of items sorted based on the TrueSkill algorithm.
        """
        return [k for k, _ in sorted(self.ratings.items(), key=lambda x: x[1])]

    def is_finished(self) -> bool:
        """
        Check if the sorting process is finished.

        Returns:
            True if the sorting process is finished, False otherwise.
        """

        if (self.comp_count >= self.comparison_max or
                self.overlap_matrix.max() <= 0):
            return True

        return False

    def comparison_is_available(self, user_id: str) -> bool:
        """
        Check if a comparison is available for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            True if a comparison is available, False otherwise.
        """
        return not self.is_finished() or not self.get_comparison(user_id)

    def get_comparison_count(self) -> int:
        """
        Get the number of comparisons performed.

        Returns:
            The number of comparisons performed.
        """
        return self.comp_count

    def get_comparison_max(self) -> int:
        """
        Get the maximum number of comparisons allowed.

        Returns:
            The maximum number of comparisons allowed.
        """
        return self.comparison_max


class RatingAlgorithm (SortingAlgorithm):
    """Implementation of the rating algorithm"""

    def __init__(self, data: List[Union[int, float, str]]):
        """
        Initialize the RatingAlgorithm.

        Args:
            data: The data to be rated.
        """
        self.n = len(data)
        self.data = list(data)

        self.comp_count = 0
        self.comparison_size = 1
        self.user_ratings = {}

    def get_comparison(self, user_id: str) -> List[Union[int, float, str]]:
        """
        Get a comparison for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            A list containing the key of the item to be rated by the user.
        """
        user_dict = self.get_user(user_id)
        if user_dict['toRate']:
            return user_dict['toRate'][0]
        return []

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get the user's dictionary.

        Args:
            user_id: The ID of the user.

        Returns:
            The dictionary containing the user's data.
        """
        if user_id not in self.user_ratings:
            user_hash = abs(hash(user_id)) % (10 ** 8)
            to_sort = copy.deepcopy(self.data)
            random.Random(user_hash).shuffle(to_sort)
            self.user_ratings[user_id] = {
                'toRate': to_sort, 'rated': {}}
        return self.user_ratings[user_id]

    def inference(
            self, user_id: str, key: Union[int, float, str],
            rating: Any):
        """
        Perform the inference step based on the user's choices.

        Args:
            user_id: The ID of the user.
            keys: The keys of the items compared by the user.
            diff_lvls: The difference levels asessed by the user.
        """

        user_dict = self.get_user(user_id)

        if key in user_dict['toRate']:
            user_dict['toRate'].remove(key)
            user_dict['rated'][key] = rating
            self.comp_count += 1

    def get_result(self) -> Dict[str, Dict[Union[int, float, str], Any]]:
        """
        Get the result of the rating algorithm for all users.

        Returns:
            A dictionary containing the rated items for each user.
        """
        return ({user: self.get_user_result(user) for
                 user in self.user_ratings.keys()})

    def get_user_result(self, user_id: str) -> Dict[Union[int, float, str], Any]:
        """
        Get the result of the rating algorithm for a specific user.

        Args:
            user_id: The ID of the user.

        Returns:
            A dictionary containing the rated items for the user.
        """
        user_dict = self.get_user(user_id)
        return user_dict['rated']

    def is_finished(self) -> bool:
        """
        Check if the sorting process is finished.

        Returns:
            False (the rating algorithm never finishes)
        """
        return False  # never finished

    def comparison_is_available(self, user_id: str) -> bool:
        """
        Check if a comparison is available for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            True if a comparison is available, False otherwise.
        """
        user_dict = self.get_user(user_id)
        if len(user_dict['toRate']):
            return True
        return False

    def get_comparison_count(self) -> int:
        """
        Get the number of comparisons performed.

        Returns:
            The number of comparisons performed.
        """
        return self.comp_count

    def get_comparison_max(self) -> int:
        """
        Get the maximum number of comparisons allowed.

        Returns:
            The maximum number of comparisons allowed.
        """
        return len(self.data)


class HybridTrueSkill (SortingAlgorithm):
    """Implementation of the rating and TrueSkill hybrid algorithm"""

    def __init__(
            self, data: List[Union[int, float, str]],
            comparison_size: int = 2, comparison_max: Optional[int] = None):
        """
        Initialize the HybridTrueSkill algorithm.

        Args:
            data: The data to be sorted.
            comparison_size: The size of each comparison.
            comparison_max: The maximum number of comparisons allowed.
        """

        self.data = data
        self.comparison_size = comparison_size
        self.comparison_max = comparison_max

        self.sort_alg = RatingAlgorithm(data)
        self.is_rating = True

    def get_comparison(self, user_id: str) -> List[Union[int, float, str]]:
        """
        Get a comparison for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            A list containing the key of the item to be compared by the user.
        """
        return self.sort_alg.get_comparison("hybrid")

    def inference(
            self, user_id: str, key: Union[int, float, str],
            rating: Any):
        """
        Perform the inference step based on the user's assessments.

        Args:
            user_id: The ID of the user.
            key: The key of the item compared by the user.
            rating: The rating assessed by the user to the item.

        Returns:
            None
        """
        self.sort_alg.inference("hybrid", key, rating)

        if self.is_rating:
            if not self.sort_alg.comparison_is_available("hybrid"):
                self.change_to_trueskill("hybrid")

    def get_result(self) -> Dict[str, Dict[Union[int, float, str], Any]]:
        """
        Get the result of the hybrid algorithm.

        Returns:
            A dictionary containing the rated items for each user.
        """
        return self.sort_alg.get_result()

    def is_finished(self) -> bool:
        """
        Check if the sorting process is finished.

        Returns:
            True if the sorting process is finished, False otherwise.
        """
        return self.sort_alg.is_finished()

    def comparison_is_available(self, user_id: str) -> bool:
        """
        Check if a comparison is available for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            True if a comparison is available, False otherwise.
        """
        return self.sort_alg.comparison_is_available("hybrid")

    def change_to_trueskill(self, user_id: str):
        """
        Change the algorithm to use the TrueSkill method.

        Args:
            user_id: The ID of the user.
        """
        # TODO: Add variable threshold for exclusion (v > threshold) as well as
        # standard deviation for TS

        results = {
            k: self.rating_to_mu(v) for k,
            v in self.sort_alg.get_user_result("hybrid").items()}  # if v > 1}

        sigma = 5

        self.sort_alg = TrueSkill(
            results.keys(),
            comparison_size=self.comparison_size,
            comparison_max=800,  # len(results.keys()) * 4,
            initial_mus=results, initial_std=sigma)
        self.is_rating = False

    def rating_to_mu(self, rating: int) -> float:
        """
        Convert a rating to the TrueSkill mu value.

        Args:s
            rating: The rating value.

        Returns:
            The corresponding mu value.
        """
        # With mu = 25 and 1/2 standard deviation spacing
        # TODO: Now assumes a 5 rating scale, could be generalized to more/less granular
        # scales
        return 25 + ((rating - 2) * 2) / 4 * 8.333

    def get_comparison_count(self) -> int:
        """
        Get the number of comparisons performed.

        Returns:
            The number of comparisons performed.
        """

        total = self.sort_alg.get_comparison_count()
        if not self.is_rating:
            total += len(self.data)

        return total

    def get_comparison_max(self) -> int:
        """
        Get the maximum number of comparisons allowed.

        Returns:
            The maximum number of comparisons allowed.
        """

        total = self.sort_alg.get_comparison_max()
        if not self.is_rating:
            total += len(self.data)

        return total
