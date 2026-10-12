import torch
import torch.nn as nn


class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()

        self.block = nn.Sequential(
            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=3,
                padding=1,
                bias=False
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),

            nn.Conv2d(
                out_channels,
                out_channels,
                kernel_size=3,
                padding=1,
                bias=False
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.block(x)


class SNUNetCD(nn.Module):
    """
    Simplified SNUNet-CD style Siamese nested U-Net
    for binary change detection.

    Input:
        x1 = image from 2020 [B, 3, H, W]
        x2 = image from 2024 [B, 3, H, W]

    Output:
        change logits [B, 1, H, W]
    """

    def __init__(self, in_channels=3, out_channels=1):
        super().__init__()

        # Encoder channels
        filters = [32, 64, 128, 256]

        # Shared encoder
        self.conv0 = ConvBlock(in_channels, filters[0])
        self.conv1 = ConvBlock(filters[0], filters[1])
        self.conv2 = ConvBlock(filters[1], filters[2])
        self.conv3 = ConvBlock(filters[2], filters[3])

        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        # Decoder
        self.up2 = nn.ConvTranspose2d(
            filters[3],
            filters[2],
            kernel_size=2,
            stride=2
        )

        self.dec2 = ConvBlock(
            filters[2] * 2,
            filters[2]
        )

        self.up1 = nn.ConvTranspose2d(
            filters[2],
            filters[1],
            kernel_size=2,
            stride=2
        )

        self.dec1 = ConvBlock(
            filters[1] * 2,
            filters[1]
        )

        self.up0 = nn.ConvTranspose2d(
            filters[1],
            filters[0],
            kernel_size=2,
            stride=2
        )

        self.dec0 = ConvBlock(
            filters[0] * 2,
            filters[0]
        )

        # Final binary prediction
        self.final = nn.Conv2d(
            filters[0],
            out_channels,
            kernel_size=1
        )

    def encode(self, x):
        x0 = self.conv0(x)
        x1 = self.conv1(self.pool(x0))
        x2 = self.conv2(self.pool(x1))
        x3 = self.conv3(self.pool(x2))

        return x0, x1, x2, x3

    def forward(self, x1, x2):

        # Siamese encoder
        x10, x11, x12, x13 = self.encode(x1)
        x20, x21, x22, x23 = self.encode(x2)

        # Difference features
        d3 = torch.abs(x13 - x23)
        d2 = torch.abs(x12 - x22)
        d1 = torch.abs(x11 - x21)
        d0 = torch.abs(x10 - x20)

        # Decoder
        u2 = self.up2(d3)
        u2 = torch.cat([u2, d2], dim=1)
        u2 = self.dec2(u2)

        u1 = self.up1(u2)
        u1 = torch.cat([u1, d1], dim=1)
        u1 = self.dec1(u1)

        u0 = self.up0(u1)
        u0 = torch.cat([u0, d0], dim=1)
        u0 = self.dec0(u0)

        # Raw logits
        output = self.final(u0)

        return output