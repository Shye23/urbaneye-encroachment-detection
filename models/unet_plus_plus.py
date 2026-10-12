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


class UNetPlusPlus(nn.Module):
    """
    Simplified U-Net++ baseline for bi-temporal change detection.

    2020 and 2024 images are concatenated to form a 6-channel input.
    Nested decoder connections provide additional feature fusion.
    """

    def __init__(self, in_channels=6, out_channels=1):

        super().__init__()

        filters = [32, 64, 128, 256]

        self.pool = nn.MaxPool2d(
            kernel_size=2,
            stride=2
        )

        # Encoder
        self.conv00 = ConvBlock(
            in_channels,
            filters[0]
        )

        self.conv10 = ConvBlock(
            filters[0],
            filters[1]
        )

        self.conv20 = ConvBlock(
            filters[1],
            filters[2]
        )

        self.conv30 = ConvBlock(
            filters[2],
            filters[3]
        )

        # Upsampling
        self.up10 = nn.ConvTranspose2d(
            filters[1],
            filters[0],
            kernel_size=2,
            stride=2
        )

        self.up20 = nn.ConvTranspose2d(
            filters[2],
            filters[1],
            kernel_size=2,
            stride=2
        )

        self.up30 = nn.ConvTranspose2d(
            filters[3],
            filters[2],
            kernel_size=2,
            stride=2
        )

        # Nested nodes
        self.conv01 = ConvBlock(
            filters[0] * 2,
            filters[0]
        )

        self.conv11 = ConvBlock(
            filters[1] * 2,
            filters[1]
        )

        self.conv21 = ConvBlock(
            filters[2] * 2,
            filters[2]
        )

        self.conv02 = ConvBlock(
            filters[0] * 3,
            filters[0]
        )

        self.conv12 = ConvBlock(
            filters[1] * 3,
            filters[1]
        )

        self.conv03 = ConvBlock(
            filters[0] * 4,
            filters[0]
        )

        self.up11 = nn.ConvTranspose2d(
            filters[1],
            filters[0],
            kernel_size=2,
            stride=2
        )

        self.up21 = nn.ConvTranspose2d(
            filters[2],
            filters[1],
            kernel_size=2,
            stride=2
        )

        self.up12 = nn.ConvTranspose2d(
            filters[1],
            filters[0],
            kernel_size=2,
            stride=2
        )

        self.final = nn.Conv2d(
            filters[0],
            out_channels,
            kernel_size=1
        )

    def forward(self, x2020, x2024):

        # Combine dates
        x = torch.cat(
            [x2020, x2024],
            dim=1
        )

        # Encoder
        x00 = self.conv00(x)

        x10 = self.conv10(
            self.pool(x00)
        )

        x20 = self.conv20(
            self.pool(x10)
        )

        x30 = self.conv30(
            self.pool(x20)
        )

        # First nested level
        x01 = self.conv01(
            torch.cat(
                [
                    x00,
                    self.up10(x10)
                ],
                dim=1
            )
        )

        x11 = self.conv11(
            torch.cat(
                [
                    x10,
                    self.up20(x20)
                ],
                dim=1
            )
        )

        x21 = self.conv21(
            torch.cat(
                [
                    x20,
                    self.up30(x30)
                ],
                dim=1
            )
        )

        # Second nested level
        x02 = self.conv02(
            torch.cat(
                [
                    x00,
                    x01,
                    self.up11(x11)
                ],
                dim=1
            )
        )

        x12 = self.conv12(
            torch.cat(
                [
                    x10,
                    x11,
                    self.up21(x21)
                ],
                dim=1
            )
        )

        # Third nested level
        x03 = self.conv03(
            torch.cat(
                [
                    x00,
                    x01,
                    x02,
                    self.up12(x12)
                ],
                dim=1
            )
        )

        output = self.final(x03)

        return output