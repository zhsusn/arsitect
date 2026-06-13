"""Tests for pagination DTOs and utilities."""

from __future__ import annotations

import pytest

from app.core.pagination import PageRequest, PageResponse


class TestPageRequest:
    """Test PageRequest validation and coercion."""

    def test_defaults(self) -> None:
        """Default page=1, page_size=50."""
        req = PageRequest()
        assert req.page == 1
        assert req.page_size == 50
        assert req.sort_order == "desc"

    def test_page_less_than_one_coerced_to_one(self) -> None:
        """page < 1 must be corrected to 1."""
        req = PageRequest(page=0)
        assert req.page == 1
        req2 = PageRequest(page=-5)
        assert req2.page == 1

    def test_page_size_greater_than_200_coerced_to_200(self) -> None:
        """page_size > 200 must be capped at 200."""
        req = PageRequest(page_size=500)
        assert req.page_size == 200

    def test_page_size_less_than_one_coerced_to_one(self) -> None:
        """page_size < 1 must be corrected to 1."""
        req = PageRequest(page_size=0)
        assert req.page_size == 1
        req2 = PageRequest(page_size=-10)
        assert req2.page_size == 1

    def test_valid_page_size_accepted(self) -> None:
        """page_size within [1, 200] is accepted as-is."""
        req = PageRequest(page_size=100)
        assert req.page_size == 100

    def test_offset_calculation(self) -> None:
        """OFFSET = (page - 1) * page_size."""
        req = PageRequest(page=3, page_size=20)
        assert req.offset == 40

    def test_sort_order_validation(self) -> None:
        """Only asc/desc allowed."""
        with pytest.raises(ValueError):
            PageRequest(sort_order="invalid")


class TestPageResponse:
    """Test PageResponse factory and properties."""

    def test_from_items_calculates_total_pages(self) -> None:
        """total_pages = ceil(total_count / page_size)."""
        resp = PageResponse.from_items(
            [1, 2, 3], total_count=25, page=1, page_size=10
        )
        assert resp.total_pages == 3
        assert resp.has_next is True
        assert resp.has_previous is False

    def test_has_next_false_on_last_page(self) -> None:
        """Last page has no next."""
        resp = PageResponse.from_items(
            [21, 22, 23, 24, 25], total_count=25, page=3, page_size=10
        )
        assert resp.has_next is False
        assert resp.has_previous is True

    def test_has_previous_false_on_first_page(self) -> None:
        """First page has no previous."""
        resp = PageResponse.from_items(
            [1, 2], total_count=2, page=1, page_size=10
        )
        assert resp.has_previous is False
        assert resp.has_next is False

    def test_empty_result(self) -> None:
        """Empty data set yields total_pages=0."""
        resp = PageResponse.from_items(
            [], total_count=0, page=1, page_size=50
        )
        assert resp.total_pages == 0
        assert resp.has_next is False
        assert resp.has_previous is False
