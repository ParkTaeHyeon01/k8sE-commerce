import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { fetchProduct } from "../api";

export default function ProductDetail() {
  const { product_id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchProduct(product_id)
      .then(setProduct)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [product_id]);

  if (loading) return <p className="status-msg">불러오는 중...</p>;
  if (error) return <p className="status-msg">오류: {error}</p>;
  if (!product) return null;

  return (
    <div className="detail-page">
      <button className="back-btn" onClick={() => navigate(-1)}>← 목록으로</button>

      <div className="detail-top">
        <img src={product.image_url} alt={product.name} />
        <div className="detail-info">
          <p className="category">{product.category_name}</p>
          <h2>{product.name}</h2>
          <div>
            {product.discount_rate > 0 && (
              <span className="discount-rate">{product.discount_rate}%</span>
            )}
            <span className="sale-price-big">{product.sale_price?.toLocaleString()}원</span>
          </div>
          {product.original_price > 0 && product.original_price !== product.sale_price && (
            <p className="original-price">{product.original_price?.toLocaleString()}원</p>
          )}
          {product.delivery_info && (
            <span className="delivery-badge">{product.delivery_info}</span>
          )}
        </div>
      </div>

      {product.detail_blocks?.length > 0 && (
        <div className="detail-blocks">
          {product.detail_blocks.map((block, i) =>
            block.type === "image"
              ? <img key={i} src={block.value} alt="" loading="lazy" />
              : <p key={i}>{block.value}</p>
          )}
        </div>
      )}
    </div>
  );
}
