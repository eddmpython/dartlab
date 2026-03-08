"""주요 제품 및 서비스 분석 모듈."""

from dartlab.engines.docsParser.finance.productService.pipeline import productService
from dartlab.engines.docsParser.finance.productService.types import ProductServiceResult

__all__ = ["productService", "ProductServiceResult"]
