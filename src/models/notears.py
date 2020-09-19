import logging
import tensorflow as tf

from helpers.dir_utils import create_dir
from helpers.tf_utils import print_summary


class NoTears(object):
    _logger = logging.getLogger(__name__)

    def __init__(self, n, d, seed=8, l1_lambda=0, use_float64=False):
        self.print_summary = print_summary    # Print summary for tensorflow variables

        self.n = n
        self.d = d
        self.seed = seed
        self.l1_lambda = l1_lambda
        self.tf_float_type = tf.dtypes.float64 if use_float64 else tf.dtypes.float32        

        # Initializer (for reproducibility)
        self.initializer = tf.keras.initializers.glorot_uniform(seed=self.seed)

        self._build()
        self._init_session()
        self._init_saver()

    def _init_session(self):
        self.sess = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(
            gpu_options=tf.compat.v1.GPUOptions(
                per_process_gpu_memory_fraction=0.5,
                allow_growth=True,
            )
        ))

    def _init_saver(self):
        self.saver = tf.compat.v1.train.Saver()

    def _build(self):
        tf.compat.v1.reset_default_graph()

        self.rho = tf.compat.v1.placeholder(self.tf_float_type)
        self.alpha = tf.compat.v1.placeholder(self.tf_float_type)
        self.lr = tf.compat.v1.placeholder(self.tf_float_type)

        self.X = tf.compat.v1.placeholder(self.tf_float_type, shape=[self.n, self.d])
        W = tf.Variable(tf.zeros([self.d, self.d], self.tf_float_type))

        self.W_prime = self._preprocess_graph(W)
        self.mse_loss = self._get_mse_loss(self.X, self.W_prime)

        self.h = tf.linalg.trace(tf.linalg.expm(self.W_prime * self.W_prime)) - self.d    # Acyclicity
        self.loss = 0.5 / self.n * self.mse_loss \
                    + self.l1_lambda * tf.norm(self.W_prime, ord=1) \
                    + self.alpha * self.h + 0.5 * self.rho * self.h * self.h

        self.train_op = tf.compat.v1.train.AdamOptimizer(learning_rate=self.lr).minimize(self.loss)
        self._logger.debug('Finished building Tensorflow graph')

    def _preprocess_graph(self, W):
        # Mask the diagonal entries of graph
        return tf.linalg.set_diag(W, tf.zeros(W.shape[0], dtype=self.tf_float_type))

    def _get_mse_loss(self, X, W_prime):
        X_prime = tf.matmul(X, W_prime)      
        return tf.square(tf.linalg.norm(X - X_prime))

    def save(self, model_dir):
        create_dir(model_dir)
        self.saver.save(self.sess, '{}/model'.format(model_dir))

    @property
    def logger(self):
        try:
            return self._logger
        except:
            raise NotImplementedError('self._logger does not exist!')


if __name__ == '__main__':
    n, d = 3000, 20
    model = NoTears(n, d)
    model.print_summary(print)

    print()
    print('model.W_prime: {}'.format(model.W_prime))
    print('model.mse_loss: {}'.format(model.mse_loss))
    print('model.h: {}'.format(model.h))
    print('model.loss: {}'.format(model.loss))
    print('model.train_op: {}'.format(model.train_op))

