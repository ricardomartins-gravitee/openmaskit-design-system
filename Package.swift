// swift-tools-version: 5.9
import PackageDescription

let package = Package(
  name: "OpenMaskitDesignSystem",
  platforms: [.macOS(.v14)],
  products: [.library(name: "OpenMaskitDesign", targets: ["OpenMaskitDesign"])],
  targets: [
    .target(name: "OpenMaskitDesign"),
    .testTarget(
      name: "OpenMaskitDesignTests", dependencies: ["OpenMaskitDesign"],
      path: "tests/OpenMaskitDesignTests"),
  ]
)
