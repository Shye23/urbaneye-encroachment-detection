import torch

print("=" * 60)
print("GPU TEST")
print("=" * 60)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Using device:", device)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("CUDA:", torch.version.cuda)

    # Create tensors directly on GPU
    a = torch.randn(2000, 2000, device=device)
    b = torch.randn(2000, 2000, device=device)

    # GPU computation
    c = torch.matmul(a, b)

    print("Tensor device:", c.device)
    print("Tensor shape:", c.shape)
    print("Computation successful!")

    # Make sure computation is finished
    torch.cuda.synchronize()

    print("GPU computation completed successfully.")

else:
    print("CUDA is NOT available.")

print("=" * 60)