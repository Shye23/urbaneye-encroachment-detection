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


class SiameseUNet(nn.Module):
    """
    Siamese U-Net for bi-temporal change detection.

    Both dates pass through the same encoder.
    Absolute feature differences are then decoded.

    Input:
        2020: [B, 3, H, W]
        2024: [B, 3, H, W]

    Output:
        [B, 1, H, W]
    """

    def __init__(self, in_channels=3, out_channels=1):

        super().__init__()

        filters = [32, 64, 128, 256]

        # Shared encoder
        self.enc0 = ConvBlock(
            in_channels,
            filters[0]
        )

        self.enc1 = ConvBlock(
            filters[0],
            filters[1]
        )

        self.enc2 = ConvBlock(
            filters[1],
            filters[2]
        )

        self.enc3 = ConvBlock(
            filters[2],
            filters[3]
        )

        self.pool = nn.MaxPool2d(
            kernel_size=2,
            stride=2
        )

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

        self.final = nn.Conv2d(
            filters[0],
            out_channels,
            kernel_size=1
        )

    def encode(self, x):

        x0 = self.enc0(x)

        x1 = self.enc1(
            self.pool(x0)
        )

        x2 = self.enc2(
            self.pool(x1)
        )

        x3 = self.enc3(
            self.pool(x2)
        )

        return x0, x1, x2, x3

    def forward(self, x2020, x2024):

        # Shared encoder
        f2020_0, f2020_1, f2020_2, f2020_3 = self.encode(
            x2020
        )

        f2024_0, f2024_1, f2024_2, f2024_3 = self.encode(
            x2024
        )

        # Feature differences
        d0 = torch.abs(
            f2020_0 - f2024_0
        )

        d1 = torch.abs(
            f2020_1 - f2024_1
        )

        d2 = torch.abs(
            f2020_2 - f2024_2
        )

        d3 = torch.abs(
            f2020_3 - f2024_3
        )

        # Decoder
        u2 = self.up2(d3)

        u2 = torch.cat(
            [u2, d2],
            dim=1
        )

        u2 = self.dec2(u2)

        u1 = self.up1(u2)

        u1 = torch.cat(
            [u1, d1],
            dim=1
        )

        u1 = self.dec1(u1)

        u0 = self.up0(u1)

        u0 = torch.cat(
            [u0, d0],
            dim=1
        )

        u0 = self.dec0(u0)

        output = self.final(u0)

        return output