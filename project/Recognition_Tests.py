from project import Recognizer as rec
from project import utils
import cv2.cv2 as cv
import json


def k_fold_cross_validation():
    """
    Placeholder method
    :return:
    """
    s = set()
    return s


def create_distance_matrix(test_csv, resize, model, height):
    matrix = dict()

    label_to_file, files = utils.read_csv(test_csv, resize=resize, mapping=True)

    for file in files:
        label = utils.get_label(file)
        matrix[(file, label)] = rec.predict(model=model, height=height, resize=resize,
                                            probe_label=label, probe_image=file, identification=True)

    return matrix


def evaluate_performances(model, thresholds, train_csv, test_csv, resize=False):
    model, height = rec.train_recongizer(model, train_csv, resize)

    distance_matrix = create_distance_matrix(test_csv, resize, model=model, height=height)

    performances = dict()
    for t in thresholds:
        genuine_attempts = 0
        impostor_attempts = 0

        fa = 0  # False accepts counter
        fr = 0  # False rejects counter
        gr = 0  # Genuine rejects counter
        di = dict()  # Correct detect and identification @ rank k counter
        di[1] = 0
        for probe in distance_matrix.keys():
            probe_label = probe[1]

            results = distance_matrix[probe]

            gallery_labels = {x[0] for x in results}

            first_result = results[0]
            fr_label = first_result[0]
            fr_distance = first_result[1]

            # Impostor attempt
            if fr_label not in gallery_labels:
                impostor_attempts += 1

                if fr_distance <= t:
                    fa += 1
                else:
                    gr += 1
                continue

            genuine_attempts += 1

            # Check if a correct identification @ rank 1 happened
            if first_result[0] == probe_label:
                # Check if distance is less than the threshold
                if fr_distance <= t:
                    di[1] += 1
                else:
                    fr += 1
                continue

            for k in range(1, len(results)):
                res = results[k]
                res_label = res[0]
                res_distance = res[1]

                if res_label == probe_label:
                    if res_distance <= t:
                        di[k] = di[k] + 1 if k in di.keys() else 1  # Correct detect & identify @ rank k
                    else:
                        fr += 1
                        break
                elif res_distance <= t:
                    fr += 1
                    continue
                elif res_distance > t:  # Just "else" might be enough
                    fr += 1
                    break

        # Compute rates
        dir_k = dict()  # Correct detect & identify rate @ rank k
        dir_k[1] = di[1] / genuine_attempts
        frr = 1 - dir_k[1]
        far = fa / impostor_attempts
        grr = gr / impostor_attempts

        higher_ranks = sorted(list(di.keys()))
        higher_ranks.remove(1)
        for k in higher_ranks:
            dir_k = (di[k] / genuine_attempts) + dir_k[k - 1]

        performances[t] = dict([("frr", frr), ("far", far), ("grr", grr), ("dir", dir_k)])

    return performances


def serialize_matrix(matrix, out_file):
    # TODO test
    with open(out_file, "w+") as fi:
        ob = json.dumps(matrix)
        fi.write(ob)


def load_matrix(file):
    # TODO test
    with open(file, "r+") as fi:
        return json.loads(fi.read())


if __name__ == '__main__':
    recognizer: cv.face_BasicFaceRecognizer = cv.face.EigenFaceRecognizer_create()
    test_thresholds = [1.0, 2.0]

    k_fold_files = k_fold_cross_validation()

    avg_far = 0
    avg_frr = 0
    avg_grr = 0
    avg_dir_k = dict()

    for train, test in k_fold_files:
        perf = evaluate_performances(model=recognizer, thresholds=test_thresholds, resize=True,
                                     train_csv=train, test_csv=test)

        # TODO Compute averages for every iteration
