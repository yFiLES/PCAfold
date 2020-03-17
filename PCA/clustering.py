import numpy as np
import random
import time

def degrade_clusters(idx, verbose=False):
    """
    This function renumerates clusters if either of these two cases is true:
        (1) `idx` is composed of non-consecutive integers, or:
        (2) the smallest cluster number in `idx` is not equal to 0.

    Example:
    ----------
    If from a clustering technique you get an `idx` that is the following:

    `[0, 0, 2, 0, 5, 10]`

    this function would turns this `idx` to:

    `[0, 0, 1, 0, 2, 3]`

    where clusters are numbered with consecutive integers.

    Alternatively, if the `idx` is the following:

    `[1, 1, 2, 2, 3, 3]`

    this function would turns this `idx` to:

    `[0, 0, 1, 1, 2, 2]`

    in order to make the smallest cluster number equal to 0.

    Input:
    ----------
    `idx`      - vector of indices classifying observations to clusters.
                 The first cluster has index 0.

    Output:
    ----------
    `idx_degraded`
               - vector of indices classifying observations to clusters.
                 The first cluster has index 0.
    `k_update` - the updated number of clusters.
    """

    index = 0
    dictionary = {}
    sorted = np.unique(idx)
    k_init = np.max(idx) + 1
    dictionary[sorted[0]] = 0
    old_val = sorted[0]
    idx_degraded = [0 for i in range(0, len(idx))]

    for val in sorted:
        if val > old_val:
            index += 1
        dictionary[val] = index

    for i, val in enumerate(idx):
        idx_degraded[i] = dictionary[val]

    k_update = np.max(idx_degraded) + 1

    if verbose == True:
        print('Clusters have been degraded.')
        print('The number of clusters have been reduced from ' + str(k_init) + ' to ' + str(k_update) + '.')

    return (idx_degraded, k_update)

def variable_bins(var, k, verbose=False):
    """
    This function does clustering based on dividing a variable vector `var` into
    bins of equal lengths.

    var_min                                               var_max
       |----------|----------|----------|----------|----------|
          bin 1      bin 2      bin 3       bin 4     bin 5

    Input:
    ----------
    `var`      - vector of variable values.
    `k`        - number of clusters to partition the data.

    Output:
    ----------
    `idx`      - vector of indices classifying observations to clusters.
                 The first cluster has index 0.
    """

    # Check that the number of clusters is an integer and is non-zero:
    if not (isinstance(k, int) and k > 0):
        raise ValueError("The number of clusters must be a positive integer.")

    var_min = np.min(var)
    var_max = np.max(var)
    bin_length = (var_max - var_min)/k
    idx = []
    bins_borders = []

    for cl in range(0,k+1):
        if cl == k+1:
            bins_borders.append(var_max)
        else:
            bins_borders.append(cl*bin_length + var_min)

    # Split into bins of variable:
    for val in var:
        if val == var_max:
            idx.append(k-1)
        else:
            for cl in range(0,k):
                if (val >= bins_borders[cl]) and (val < bins_borders[cl+1]):
                    idx.append(cl)

    # Degrade clusters if needed:
    if np.size(np.unique(idx)) != k:
        (idx, k) = degrade_clusters(idx, verbose)

    return(np.asarray(idx))

def mixture_fraction_bins(Z, k, Z_stoich):
    """
    This function does clustering based on dividing a mixture fraction vector
    `Z` into bins of equal lengths. The vector is first split to lean and rich
    side and then the sides get divided further into clusters. When k is even,
    this function will always create equal number of clusters on the lean and
    rich side. When k is odd, there will be one more cluster on the rich side
    compared to the lean side.

    Z_min           Z_stoich                                 Z_max
       |-------|-------|------------|------------|------------|
         bin 1   bin 2     bin 3        bin 4         bin 5

    Input:
    ----------
    `Z`        - vector of mixture fraction values.
    `k`        - number of clusters to partition the data.
    `Z_stoich` - stoichiometric mixture fraction.

    Output:
    ----------
    `idx`      - vector of indices classifying observations to clusters.
                 The first cluster has index 0.
    """

    # Check that the number of clusters is an integer and is non-zero:
    if not (isinstance(k, int) and k > 0):
        raise ValueError("The number of clusters must be a positive integer.")

    # Number of interval borders:
    n_bins_borders = k + 1

    # Minimum and maximum mixture fraction:
    min_Z = np.min(Z)
    max_Z = np.max(Z)

    # Partition the Z-space:
    if k == 1:

        borders = np.linspace(min_Z, max_Z, n_bins_borders)

    else:

        # Z-space lower than stoichiometric mixture fraction:
        borders_lean = np.linspace(min_Z, Z_stoich, np.ceil(n_bins_borders/2))

        # Z-space higher than stoichiometric mixture fraction:
        borders_rich = np.linspace(Z_stoich, max_Z, np.ceil((n_bins_borders+1)/2))

        # Combine the two partitions:
        borders = np.concatenate((borders_lean[0:-1], borders_rich))

    # Bin data matrices initialization:
    idx_clust = []
    idx = np.zeros((len(Z), 1))

    # Create the cluster division vector:
    for bin in range(0,k):

        idx_clust.append([np.where((Z >= borders[bin]) & (Z <= borders[bin+1]))])
        idx[idx_clust[bin]] = bin+1

    return(idx)

def kmeans(X, k):
    """
    This function performs K-Means clustering.

    Input:
    ----------
    `X`        - conditioning variable or a data set.
    `k`        - number of clusters to partition the data.

    Output:
    ----------
    `idx`      - vector of indices classifying observations to clusters.
                 The first cluster has index 0.
    """

    # Check that the number of clusters is an integer and is non-zero:
    if not (isinstance(k, int) and k > 0):
        raise ValueError("The number of clusters must be a positive integer.")

    from sklearn.cluster import KMeans

    kmeans = KMeans(n_clusters=k, precompute_distances=True, algorithm='auto').fit(X)
    idx = kmeans.labels_

    return(idx)

def vqpca(X, k, n_pcs, scaling_criteria='NONE', idx_0=[], maximum_number_of_iterations=600):
    """
    This function performs Vector Quantization clustering using
    Principal Component Analysis.

    VQPCA algorithm will center the global data set by mean and scale the global
    data set by the scaling specified in the `scaling_criteria` parameter.

    Note that the data in local cluster clusters will still be centered by the
    mean but will not be scaled!

    Input:
    ----------
    `X`        - raw data set, uncentered and unscaled.
    `k`        - number of clusters to partition the data.
    `n_pcs`    - number of Principal Components that will be used to reconstruct
                 the data at each iteration.

    Output:
    ----------
    `idx`      - vector of indices classifying observations to clusters.
                 The first cluster has index 0.
    """

    import PCA.PCA as PCA
    import numpy.linalg
    from sklearn.decomposition import PCA as sklPCA

    (n_obs, n_vars) = np.shape(X)

    # Check that the provided idx_0 has the same number of entries as there are observations in X:
    if len(idx_0) > 0:
        if len(idx_0) != n_obs:
            raise ValueError("The number of observations in the data set `X` must match the number of elements in `idx` vector.")

    # Initialize parameters:
    convergence = 0
    iteration = 0
    eps_rec = 1.0
    eps_rec_min = 1.0e-02

    # Tolerance for cluster centroids:
    a_tol = 1.0e-16

    # Tolerance for the error:
    r_tol = 1.0e-08

    # Initialize the eigenvectors matrix:
    eigenvectors = []

    # Initialize the scalings matrix:
    scalings = []

    for i in range(0,k):
        eigenvectors.append(np.eye(n_vars, n_pcs))
        scalings.append(np.ones((n_vars,)))

    # Maximum number of Principal Components:
    n_pcs_max = n_pcs

    # Center and scale the data:
    (X_pre_processed, _, _) = PCA.center_scale(X, scaling_criteria)

    # Initialization of cluster centroids:
    if len(idx_0) > 0:

        # If there is a user provided initial idx_0, find the initial centroids:
        centroids = get_centroids(scal_X, idx_0)

    else:

        # Initialize centroids automatically as observations uniformly selected from X:
        centroids_indices = [int(i) for i in np.linspace(0, n_obs-1, k+2)]
        centroids_indices.pop()
        centroids_indices.pop(0)
        centroids = X_pre_processed[centroids_indices, :]

    # VQPCA algorithm:
    while ((convergence == 0) and (iteration <= maximum_number_of_iterations)):

        print('Iteration: ' + str(iteration) + '\n----------')

        # Initialize the reconstruction error matrix:
        sq_rec_err = np.zeros((n_obs, k))

        # Initialize the convergence of the cluster centroids:
        centroids_convergence = 0

        # Initialize the convergence of the reconstruction error:s
        eps_rec_convergence = 0

        # Reconstruct the data from the low-dimensional representation, evaluate the mean squared reconstruction error:
        for j in range(0,k):

            D = np.diag(scalings[j])
            C_mat = np.tile(centroids[j, :], (n_obs, 1))

            result = np.dot(numpy.linalg.inv(D), np.dot(eigenvectors[j], np.dot(np.transpose(eigenvectors[j]), D)))
            rec_err_os = (X_pre_processed - C_mat - np.dot((X_pre_processed - C_mat), result))
            sq_rec_err[:, j] = np.sum(rec_err_os**2, axis=1)

        # Assign the observations to clusters based on the minimum reconstruction error:
        idx = np.argmin(sq_rec_err, axis = 1)
        rec_err_min = np.min(sq_rec_err, axis = 1)
        rec_err_min_rel = rec_err_min

        # Evaluate the global mean reconstruction error (single value):
        eps_rec_new = np.mean(rec_err_min_rel)

        # Partition the data observations into clusters:
        (nz_X_k, nz_idx_clust, k) = get_partition(X_pre_processed, idx)

        # Evaluate the relative recontruction errors in each cluster:
        rec_err_min_rel_k = []

        for j in range(0,k):
            rec_err_min_rel_k.append(rec_err_min_rel[nz_idx_clust[j]])

        # Evaluate the mean reconstruction error in each cluster:
        eps_rec_new_clust = np.zeros(k)
        size_clust = np.zeros(k)

        for j in range(0,k):
            eps_rec_new_clust[j] = np.mean(rec_err_min_rel_k[j])
            size_clust[j] = len(nz_X_k[j])

        print('Global mean recontruction error at iteration ' + str(iteration) + ' is ' + str(eps_rec_new))

        # Find the new cluster centroids:
        centroids_new = np.zeros((k, n_vars))

        for j in range(0,k):
            centroids_new[j, :] = np.mean(nz_X_k[j], axis=0)

        eps_rec_var = abs((eps_rec_new - eps_rec) / eps_rec_new)

        # Potentially increase the number of Principal Components in the approximation,
        # need to think it through whether we want to keep that:
        # if ((eps_rec_var < r_tol) and (eps_rec_new > eps_rec_min) and (n_eigs < n_eigs_max)):
        #     n_pcs = n_pcs + 1
        #     print('Cluster ' + str(j)+ ' dimension increased to %d \n', j,  n_eigs);


        # Judge the convergence of errors:
        if (eps_rec_var < r_tol):
            eps_rec_convergence = 1

        # Judge the convergence of centroids:
        if (len(centroids) == len(centroids_new)):
            centroids_var = abs((centroids_new - centroids) / (centroids_new + a_tol))

            # If all elements in the C_var is less than the error tolerance:
            if (centroids_var < r_tol).all():
                centroids_convergence = 1

        # If the convergence of centroids and reconstruction error is reached, the algorithm stops:
        if ((iteration > 1) and (centroids_convergence == 1) and (eps_rec_convergence == 1)):
            convergence = 1
            print('Convergence reached in iteration: ' + str(iteration))

        # Update recontruction error and cluster centroids:
        centroids = centroids_new
        eps_rec = eps_rec_new

        # Initialize the eigenvectors matrix:
        eigenvectors = []

        # Perform PCA in local clusters:
        for j in range(0,k):

            # Perform PCA:
            pca = sklPCA()
            pca.fit(nz_X_k[j])
            scores = pca.transform(nz_X_k[j])
            PCs = pca.components_
            eigenvectors.append(PCs[:,0:n_pcs])

        # Increment the iteration counter:
        iteration = iteration + 1;
        print('\n')

    if (convergence == 0):
        print('Convergence not reached in ' + str(iteration) +' iterations.');

    # Degrade clusters if needed:
    if len(np.unique(idx)) != (np.max(idx)+1):
        (idx, k_new) = degrade_clusters(idx, verbose=False)

    return(idx)

def flip_clusters(idx, dictionary):
    """
    This function flips the cluster labelling according to instructions provided
    in the dictionary. For a `dictionary = {key : value}`, a cluster with a
    number `key` will get a number `value`.

    Input:
    ----------
    `idx`      - vector of indices classifying observations to clusters.
                 The first cluster has index 0.
    `dictionary`
               - a dictionary specifying the cluster numeration flipping
                 instructions.

    Output:
    ----------
    `flipped_idx`
               - vector of indices classifying observations to clusters.
                 The first cluster has index 0.
    """

    flipped_idx = []

    for i in idx:
        if i in dictionary.keys():
            flipped_idx.append(dictionary[i])
        else:
            flipped_idx.append(i)

    return flipped_idx

def get_centroids(X, idx):
    """
    This function computes the centroids for the clustering specified in the
    `idx` vector.

    Input:
    ----------
    `X`        - data set for computing the cluster centroids.
    `idx`      - vector of indices classifying observations to clusters.
                 The first cluster has index 0.

    Output:
    ----------
    `centroids`
               - matrix of cluster centroids. It has size k times number of
                 observations.
    """

    # Degrade clusters if needed:
    if len(np.unique(idx)) != (np.max(idx)+1):
        (idx, k_new) = degrade_clusters(idx, verbose=False)

    (n_obs, n_vars) = np.shape(X)

    # Check if the number of indices in `idx` is the same as the number of observations in a data set:
    if n_obs != len(idx):
        raise ValueError("The number of observations in the data set `X` must match the number of elements in `idx` vector.")

    # Find the number of clusters:
    k = len(np.unique(idx))

    # Initialize the centroids matrix:
    centroids = np.zeros((k, n_vars))

    # Compute the centroids:
    for i in range(0,k):
        indices = [ind for ind, e in enumerate(idx) if e == i]
        centroids[i, :] = np.mean(X[indices,:], axis=0)

    return(centroids)

def get_partition(X, idx):
    """
    This function computes the centroids for the clustering specified in the
    `idx` vector.

    Input:
    ----------
    `X`        - data set for computing the cluster centroids.
    `idx`      - vector of indices classifying observations to clusters.
                 The first cluster has index 0.

    Output:
    ----------
    `centroids`
               - matrix of cluster centroids. It has size k times number of
                 observations.
    """

    (n_obs, n_vars) = np.shape(X);

    idx = np.array(idx)

    # Remove empty clusters from indexing:
    if len(np.unique(idx)) != (np.max(idx)+1):
        (idx, k_new) = PCA.clustering.degrade_clusters(idx, verbose=False)
        print('Empty clusters were removed.')

    k = len(np.unique(idx))

    idx_clust = []
    n_points = np.zeros(k)
    data_in_clusters = []
    data_idx_in_clusters = []

    for i in range(0,k):

        indices_to_append = np.argwhere(idx==i).ravel()
        idx_clust.append(indices_to_append)
        n_points[i] = len(indices_to_append)

        if (n_points[i] < n_vars):
            print('Too few points (' + str(int(n_points[i])) + ') in cluster ' + str(i) + ', cluster will be removed.')

    # Find those cluster numbers where the number of observations is not less than number of variables:
    nz_idx = np.argwhere(n_points >= n_vars).ravel()

    # Compute the new number of clusters taking into account removed clusters:
    k_new = len(nz_idx)

    for i in range(0,k_new):

        # Assign observations to clusters:
        data_idx_in_clusters.append(idx_clust[nz_idx[i]])
        data_in_clusters.append(X[data_idx_in_clusters[i],:])

    return(data_in_clusters, data_idx_in_clusters, k_new)

def test():
    """
    This function tests the `clustering` module.
    """

    (idx, k) = degrade_clusters([1,1,2,2,3,3], verbose=False)
    if np.min(idx) != 0:
        print('Test of degrade_clusters failed.')
        return 0
    if k != 3:
        print('Test of degrade_clusters failed.')
        return 0

    print('Test passed.')
    return 1
