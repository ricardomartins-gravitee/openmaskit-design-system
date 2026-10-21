import Foundation
import XCTest

@testable import OpenMaskitDesign

#if canImport(AppKit)
  import AppKit
  import SwiftUI
#endif

final class DesignTests: XCTestCase {
  func testVersionAndAliases() {
    XCTAssertEqual(OpenMaskitTokens.version, "0.1.0")
    XCTAssertEqual(OpenMaskitTokens.componentButtonRadius, OpenMaskitTokens.radiusButton)
    XCTAssertEqual(OpenMaskitTokens.componentPanelGap, OpenMaskitTokens.spaceMd)
    XCTAssertEqual(OpenMaskitTokens.componentBadgePaddingY, OpenMaskitTokens.spaceXs)
  }

  func testColorAndDurationMapping() {
    XCTAssertEqual(OpenMaskitTokens.colorBgRoot.red, 10.0 / 255, accuracy: 0.000000001)
    XCTAssertEqual(OpenMaskitTokens.colorAccentDim.alpha, 32.0 / 255, accuracy: 0.000000001)
    XCTAssertEqual(OpenMaskitTokens.durationFast, 0.15)
    XCTAssertEqual(OpenMaskitTokens.spaceLg, 16)
    XCTAssertLessThan(OpenMaskitTokens.opacityDisabled, OpenMaskitTokens.opacityPressed)
  }

  #if canImport(AppKit)
    @MainActor func testThemeUsesSRGBAndPreservesOpacity() throws {
      let root = try XCTUnwrap(NSColor(OpenMaskitTheme.root).usingColorSpace(.sRGB))
      XCTAssertEqual(root.redComponent, 10.0 / 255, accuracy: 0.001)
      let tint = try XCTUnwrap(
        NSColor(OpenMaskitTokens.colorAccentDim.color).usingColorSpace(.sRGB))
      XCTAssertEqual(tint.alphaComponent, 32.0 / 255, accuracy: 0.001)
    }

    @MainActor func testNativeComponentsRenderWithBoundedIntrinsicLayout() throws {
      _ = NSApplication.shared
      let view = VStack {
        OpenMaskitPanel("Services", detail: "Not set up") {
          Text("Synthetic fixture").font(OpenMaskitTypography.body)
          HStack {
            Button("Set Up OpenMaskit") {}.buttonStyle(OpenMaskitButtonStyle(kind: .primary))
            Button("Stop") {}.buttonStyle(OpenMaskitButtonStyle(kind: .danger)).disabled(true)
            OpenMaskitBadge(title: "Ready", color: OpenMaskitTheme.green)
          }
        }
        TextField("Name", text: .constant("Synthetic MCP"))
      }
      .padding(OpenMaskitTokens.spaceLg)
      .frame(width: 600)
      .foregroundStyle(OpenMaskitTheme.text)
      .background(OpenMaskitTheme.root)
      .preferredColorScheme(.dark)
      let host = NSHostingView(rootView: view)
      host.appearance = NSAppearance(named: .darkAqua)
      let size = host.fittingSize
      XCTAssertEqual(size.width, 600, accuracy: 1)
      XCTAssertGreaterThan(size.height, 90)
      XCTAssertLessThan(size.height, 300)
      host.frame = NSRect(origin: .zero, size: size)
      host.layoutSubtreeIfNeeded()
      let bitmap = try XCTUnwrap(host.bitmapImageRepForCachingDisplay(in: host.bounds))
      host.cacheDisplay(in: host.bounds, to: bitmap)
      XCTAssertGreaterThan(bitmap.pixelsWide, 0)
      XCTAssertGreaterThan(bitmap.pixelsHigh, 0)
      if let output = ProcessInfo.processInfo.environment["DESIGN_SNAPSHOT_DIR"] {
        let directory = URL(fileURLWithPath: output)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let png = try XCTUnwrap(bitmap.representation(using: .png, properties: [:]))
        try png.write(to: directory.appendingPathComponent("native-components.png"))
      }
      XCTAssertTrue(
        host.subviews.allSatisfy { !String(describing: type(of: $0)).contains("WebView") })
    }
  #endif
}
