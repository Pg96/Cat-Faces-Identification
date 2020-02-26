from argparse import ArgumentParser
import numpy as np

from utils import *


def norm_0_255(source: np.ndarray):
    src = source.copy()
    dst = None

    shape = source.shape
    if len(shape) == 2:  # single channel
        dst = cv.normalize(src, dst, 0, 255, cv.NORM_MINMAX, cv.CV_8UC1)
    elif len(shape) > 2 and shape[2] == 3:  # 3 channels
        dst = cv.normalize(src, dst, 0, 255, cv.NORM_MINMAX, cv.CV_8UC3)
    else:
        dst = src.copy()

    return dst


def train_recongizer(model: cv.face_BasicFaceRecognizer, csv_filename, resize=False, ret_labels=False):
    faces, labels = read_csv(csv_filename, resize)

    print("Total faces: {0}\nTotal labels: {1}".format(len(faces), len(set(labels))))

    height = faces[0].shape[0]

    # sizes = set()
    # for image in faces:
    #     sizes.add(image.shape)
    # print(sizes)

    model.train(faces, np.array(labels))

    # print("Train finished")

    if ret_labels:
        return model, height, set(labels)

    return model, height


def predict(model: cv.face_BasicFaceRecognizer, height, probe_image, probe_label=None, resize=False,
            identification=True,
            save_dir=None,
            show_mean=False,
            save_mean=False,
            show_faces=False,
            save_faces=False
            ):
    if not path.exists(probe_image):
        raise RuntimeError("File {} does not exist!".format(probe_image))

    input_face = cv.imread(probe_image, 0)

    if resize:
        input_face = resize_image(input_face, 100, 100)

    if identification:
        coll: cv.face_StandardCollector = cv.face.StandardCollector_create()
        pred = model.predict_collect(input_face, coll)
        # print(coll.getResults())
        # print(coll.getMinDist())
        # print(coll.getMinLabel())

        # results = parse_identification_results(coll.getResults())

        results = sorted(coll.getResults(), key=lambda x: x[1])

        # print(results)

        # if probe_label is not None:
        #     print("Predicted class = {0} ({1}) with confidence = {2}; Actual class = {3} ({4}).\n\t Outcome: {5}"
        #           .format(coll.getMinLabel(), get_subject_name(coll.getMinLabel()), coll.getMinDist(),
        #                   probe_label, get_subject_name(probe_label),
        #                   "Success!" if coll.getMinLabel() == probe_label else "Failure!"))

        return results

    prediction = model.predict(input_face)

    if probe_label is not None:
        print("Predicted class = {0} ({1}) with confidence = {2}; Actual class = {3} ({4}).\n\t Outcome: {5}"
              .format(prediction[0], get_subject_name(prediction[0]), prediction[1],
                      probe_label, get_subject_name(probe_label),
                      "Success!" if prediction[0] == probe_label else "Failure!"))

    if type(model) is cv.face_LBPHFaceRecognizer:
        print("Model Information:")
        model_info = "\tLBPH(radius={}, neighbors={}, grid_x={}, grid_y={}, threshold={})".format(
            model.getRadius(),
            model.getNeighbors(),
            model.getGridX(),
            model.getGridY(),
            model.getThreshold())
        print(model_info)

        histograms = model.getHistograms()
        print("Size of the histograms: " + str(histograms[0].size))

        return

    if show_mean or save_mean:
        mean = model.getMean()

        reshaped_mean = mean.reshape(height, -1)
        normalized_mean = norm_0_255(reshaped_mean)

        if show_mean:
            show_image(normalized_mean)
        elif save_mean and save_dir is not None:
            cv.imwrite(path.join(save_dir, "mean.png"), normalized_mean)

    if show_faces or save_faces:
        eigenvalues: np.ndarray = model.getEigenValues()
        eigenvectors: np.ndarray = model.getEigenVectors()

        colormap = cv.COLORMAP_JET if type(model) is cv.face_EigenFaceRecognizer else cv.COLORMAP_BONE
        faces = []

        for i in range(0, min(10, len(eigenvectors.T))):
            msg = "Eigenvalue #{0} = {1}".format(i, eigenvalues.item(i))
            print(msg)

            ev = eigenvectors[:, i].copy()
            grayscale = norm_0_255(ev.reshape(height, -1))
            cgrayscale = cv.applyColorMap(grayscale, colormap)

            if show_faces:
                faces.append(cgrayscale)
            elif save_faces and save_dir is not None:
                file_name = path.join(save_dir, "eigenface_{}.png".format(i))
                cv.imwrite(file_name, norm_0_255(cgrayscale))

        if show_faces:
            show_images(faces)

    # TODO Think about writing the reconstruction part


def save_model(model: cv.face_BasicFaceRecognizer, save_dir, height, uid=0):
    file_name = path.join(save_dir, "model_{0}_{1}.xml".format(uid, height))
    print("Saving model to: ", file_name)
    model.save(file_name)


def load_model(model: cv.face_BasicFaceRecognizer, file_name):
    model.read(file_name)
    height = file_name.split("_")[-1].split(".")[0]

    return model, int(height)


def test_aligned(model: cv.face_BasicFaceRecognizer):
    mod, hei = train_recongizer(model, "../dataset_info/bak/best/subjects_aligned.csv")
    predict(model=mod, height=hei, probe_image="../images/dataset/cropped/t/27_cropped_aligned.jpg", probe_label=7,
            show_mean=False, show_faces=False, identification=False)
    predict(model=mod, height=hei, probe_image="../images/dataset/cropped/c/9_cropped_aligned.jpeg", probe_label=0,
            show_mean=False, show_faces=False, identification=False)
    predict(model=mod, height=hei, probe_image="../images/dataset/cropped/Rudi/9_cropped_aligned.jpeg", probe_label=5,
            show_mean=False, show_faces=False, identification=False)
    # save_model(mod, hei)

    # mod2, hei2 = load_model(models_dir+"eigenfaces/model_0_200.xml")
    # predict(model=mod2, height=hei2, face="../images/dataset/cropped/t/27_cropped_aligned.jpg", sample_label=1,
    #         show_mean=False, show_faces=False)
    # predict(model=mod2, height=hei2, face="../images/dataset/cropped/c/9_cropped_aligned.jpeg", sample_label=0,
    #         show_mean=False, show_faces=False)


def test_cropped(model: cv.face_BasicFaceRecognizer):
    mod, hei = train_recongizer(model, "../dataset_info/bak/best/subjects.csv", resize=True)
    predict(model=mod, height=hei, resize=True, probe_image="../images/dataset/cropped/s1/27.jpg", probe_label=1,
            show_mean=False, show_faces=True, identification=False)
    predict(model=mod, height=hei, resize=True, probe_image="../images/dataset/cropped/s2/10.jpg", probe_label=2,
            show_mean=False, show_faces=False, identification=False)
    predict(model=mod, height=hei, resize=True, probe_image="../images/dataset/cropped/s8/22.jpg", probe_label=8,
            show_mean=False, show_faces=False, identification=False)
    # save_model(mod, hei)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-r', '--recognizer', help='The recognizer to use', type=int, choices=range(3), required=True)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    model: cv.face_BasicFaceRecognizer = cv.face.EigenFaceRecognizer_create()

    # TODO check params
    if args.recognizer == 0:
        # model: cv.face_BasicFaceRecognizer = cv.face.EigenFaceRecognizer_create(num_components=30000)
        # model: cv.face_BasicFaceRecognizer = cv.face.EigenFaceRecognizer_create(threshold=2350.0)
        # model: cv.face_BasicFaceRecognizer = cv.face.EigenFaceRecognizer_create(threshold=100.0, num_components=10)
        model: cv.face_BasicFaceRecognizer = cv.face.EigenFaceRecognizer_create()

    elif args.recognizer == 1:
        model: cv.face_BasicFaceRecognizer = cv.face.FisherFaceRecognizer_create()

    elif args.recognizer == 2:
        model: cv.face_BasicFaceRecognizer = cv.face.LBPHFaceRecognizer_create()

    # test_aligned(model)
    test_cropped(model)
