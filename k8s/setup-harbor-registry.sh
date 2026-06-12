#!/bin/bash
# 모든 k8s 노드에 Harbor insecure registry 설정 추가

HARBOR_IP="192.168.0.54"
NODES=("192.168.0.68" "192.168.0.57" "192.168.0.59" "192.168.0.60")

HOSTS_TOML=$(cat <<EOF
server = "https://${HARBOR_IP}"

[host."https://${HARBOR_IP}"]
  capabilities = ["pull", "resolve"]
  skip_verify = true
EOF
)

for NODE in "${NODES[@]}"; do
    echo "=== $NODE 설정 중 ==="
    ssh "$NODE" "
        sudo mkdir -p /etc/containerd/certs.d/${HARBOR_IP}
        echo '${HOSTS_TOML}' | sudo tee /etc/containerd/certs.d/${HARBOR_IP}/hosts.toml
        sudo systemctl restart containerd
        echo '완료'
    "
done

echo "=== 전체 완료 ==="
