"""Algorithms for linear algebra."""

from __future__ import annotations

import galois
import numpy as np
import numpy.typing as npt
import sympy as sp


class MatGF2:
    """Matrix on GF2 field."""

    def __init__(self, data):
        """Construct a matrix of GF2.

        Parameters
        ----------
        data: array_like
            input data
        """
        if isinstance(data, MatGF2):
            self.data = data.data
        else:
            self.data = galois.GF2(data)

    def __repr__(self) -> str:
        """Return the representation string of the matrix."""
        return repr(self.data)

    def __str__(self) -> str:
        """Return the displayable string of the matrix."""
        return str(self.data)

    def __eq__(self, other: MatGF2) -> bool:
        """Return `True` if two matrices are equal, `False` otherwise."""
        return np.all(self.data == other.data)

    def __add__(self, other: npt.NDArray | MatGF2) -> MatGF2:
        """Add two matrices."""
        if isinstance(other, np.ndarray):
            other = MatGF2(other)
        return MatGF2(self.data + other.data)

    def __sub__(self, other: npt.NDArray | MatGF2) -> MatGF2:
        """Substract two matrices."""
        if isinstance(other, np.ndarray):
            other = MatGF2(other)
        return MatGF2(self.data - other.data)

    def __mul__(self, other: npt.NDArray | MatGF2) -> MatGF2:
        """Compute the point-wise multiplication of two matrices."""
        if isinstance(other, np.ndarray):
            other = MatGF2(other)
        return MatGF2(self.data * other.data)

    def __matmul__(self, other: npt.NDArray | MatGF2) -> MatGF2:
        """Multiply two matrices."""
        if isinstance(other, np.ndarray):
            other = MatGF2(other)
        return MatGF2(self.data @ other.data)

    def copy(self) -> MatGF2:
        """Return a copy of the matrix."""
        return MatGF2(self.data.copy())

    def add_row(self, array_to_add=None, row=None) -> None:
        """Add a row to the matrix.

        Parameters
        ----------
        array_to_add: array_like(optional)
            row to add. Defaults to None. if None, add a zero row.
        row: int(optional)
            index to add a new row. Defaults to None.
        """
        if row is None:
            row = self.data.shape[0]
        if array_to_add is None:
            array_to_add = np.zeros((1, self.data.shape[1]), dtype=int)
        array_to_add = array_to_add.reshape((1, self.data.shape[1]))
        self.data = np.insert(self.data, row, array_to_add, axis=0)

    def add_col(self, array_to_add=None, col=None) -> None:
        """Add a column to the matrix.

        Parameters
        ----------
        array_to_add: array_like(optional)
            column to add. Defaults to None. if None, add a zero column.
        col: int(optional)
            index to add a new column. Defaults to None.
        """
        if col is None:
            col = self.data.shape[1]
        if array_to_add is None:
            array_to_add = np.zeros((1, self.data.shape[0]), dtype=int)
        array_to_add = array_to_add.reshape((1, self.data.shape[0]))
        self.data = np.insert(self.data, col, array_to_add, axis=1)

    def concatenate(self, other: MatGF2, axis: int = 1) -> None:
        """Concatinate two matrices.

        Parameters
        ----------
        other: MatGF2
            matrix to concatinate
        axis: int(optional)
            axis to concatinate. Defaults to 1.
        """
        self.data = np.concatenate((self.data, other.data), axis=axis)

    def remove_row(self, row: int) -> None:
        """Remove a row from the matrix.

        Parameters
        ----------
        row: int
            index to remove a row
        """
        self.data = np.delete(self.data, row, axis=0)

    def remove_col(self, col: int) -> None:
        """Remove a column from the matrix.

        Parameters
        ----------
        col: int
            index to remove a column
        """
        self.data = np.delete(self.data, col, axis=1)

    def swap_row(self, row1: int, row2: int) -> None:
        """Swap two rows.

        Parameters
        ----------
        row1: int
            row index
        row2: int
            row index
        """
        self.data[[row1, row2]] = self.data[[row2, row1]]

    def swap_col(self, col1: int, col2: int) -> None:
        """Swap two columns.

        Parameters
        ----------
        col1: int
            column index
        col2: int
            column index
        """
        self.data[:, [col1, col2]] = self.data[:, [col2, col1]]

    def permute_row(self, row_permutation) -> None:
        """Permute rows.

        Parameters
        ----------
        row_permutation: array_like
            row permutation
        """
        self.data = self.data[row_permutation, :]

    def permute_col(self, col_permutation) -> None:
        """Permute columns.

        Parameters
        ----------
        col_permutation: array_like
            column permutation
        """
        self.data = self.data[:, col_permutation]

    def is_canonical_form(self) -> bool:
        """Check if the matrix is in a canonical form (row reduced echelon form).

        Returns
        -------
        bool: bool
            True if the matrix is in canonical form
        """
        diag = self.data.diagonal()
        nonzero_diag_index = diag.nonzero()[0]

        rank = len(nonzero_diag_index)
        for i in range(len(nonzero_diag_index)):
            if diag[nonzero_diag_index[i]] == 0:
                if np.count_nonzero(diag[i:]) != 0:
                    break
                return False

        ref_array = MatGF2(np.diag(np.diagonal(self.data[:rank, :rank])))
        if np.count_nonzero(self.data[:rank, :rank] - ref_array.data) != 0:
            return False

        return np.count_nonzero(self.data[rank:, :]) == 0

    def get_rank(self) -> int:
        """Get the rank of the matrix.

        Returns
        -------
        int: int
            rank of the matrix
        """
        mat_a = self.forward_eliminate(copy=True)[0] if not self.is_canonical_form() else self
        nonzero_index = np.diag(mat_a.data).nonzero()
        return len(nonzero_index[0])

    def forward_eliminate(self, b=None, copy=False) -> tuple[MatGF2, MatGF2, list[int], list[int]]:
        r"""Forward eliminate the matrix.

        |A B| --\ |I X|
        |C D| --/ |0 0|
        where X is an arbitrary matrix

        Parameters
        ----------
        b: array_like(otional)
            Left hand side of the system of equations. Defaults to None.
        copy: bool(optional)
            copy the matrix or not. Defaults to False.

        Returns
        -------
        mat_a: MatGF2
            forward eliminated matrix
        b: MatGF2
            forward eliminated right hand side
        row_permutation: list
            row permutation
        col_permutation: list
            column permutation
        """
        mat_a = MatGF2(self.data) if copy else self
        if b is None:
            b = np.zeros((mat_a.data.shape[0], 1), dtype=int)
        b = MatGF2(b)
        # Remember the row and column order
        row_permutation = list(range(mat_a.data.shape[0]))
        col_permutation = list(range(mat_a.data.shape[1]))

        # Gauss-Jordan Elimination
        max_rank = min(mat_a.data.shape)
        for row in range(max_rank):
            if mat_a.data[row, row] == 0:
                pivot = mat_a.data[row:, row:].nonzero()
                if len(pivot[0]) == 0:
                    break
                pivot_row = pivot[0][0] + row
                if pivot_row != row:
                    mat_a.swap_row(row, pivot_row)
                    b.swap_row(row, pivot_row)
                    former_row = row_permutation.index(row)
                    former_pivot_row = row_permutation.index(pivot_row)
                    row_permutation[former_row] = pivot_row
                    row_permutation[former_pivot_row] = row
                pivot_col = pivot[1][0] + row
                if pivot_col != row:
                    mat_a.swap_col(row, pivot_col)
                    former_col = col_permutation.index(row)
                    former_pivot_col = col_permutation.index(pivot_col)
                    col_permutation[former_col] = pivot_col
                    col_permutation[former_pivot_col] = row
                assert mat_a.data[row, row] == 1
            eliminate_rows = set(mat_a.data[:, row].nonzero()[0]) - {row}
            for eliminate_row in eliminate_rows:
                mat_a.data[eliminate_row, :] += mat_a.data[row, :]
                b.data[eliminate_row, :] += b.data[row, :]
        return mat_a, b, row_permutation, col_permutation

    def backward_substitute(self, b) -> tuple[npt.NDArray, list[sp.Symbol]]:
        """Backward substitute the matrix.

        Parameters
        ----------
        b: array_like
            right hand side of the system of equations

        Returns
        -------
        x: sympy.MutableDenseMatrix
            answer of the system of equations
        kernels: list-of-sympy.Symbol
            kernel of the matrix.
            matrix x contains sympy.Symbol if the input matrix is not full rank.
            nan-column vector means that there is no solution.
        """
        rank = self.get_rank()
        b = MatGF2(b)
        x = []
        kernels = sp.symbols(f"x0:{self.data.shape[1] - rank}")
        for col in range(b.data.shape[1]):
            x_col = []
            b_col = b.data[:, col]
            if np.count_nonzero(b_col[rank:]) != 0:
                x_col = [sp.nan for i in range(self.data.shape[1])]
                x.append(x_col)
                continue
            for row in range(rank - 1, -1, -1):
                sol = sp.true if b_col[row] == 1 else sp.false
                kernel_index = np.nonzero(self.data[row, rank:])[0]
                for k in kernel_index:
                    sol ^= kernels[k]
                x_col.insert(0, sol)
            for row in range(rank, self.data.shape[1]):
                x_col.append(kernels[row - rank])
            x.append(x_col)

        x = np.array(x).T

        return x, kernels
