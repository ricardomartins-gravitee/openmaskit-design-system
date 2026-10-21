import AppKit
import OpenMaskitDesign
import SwiftUI

@main
struct Acceptance {
  @MainActor static func main() {
    _ = NSApplication.shared
    precondition(OpenMaskitTokens.version == "0.1.0")
    precondition(OpenMaskitTokens.componentPanelGap == OpenMaskitTokens.spaceMd)
    let color = NSColor(OpenMaskitTheme.root).usingColorSpace(.sRGB)!
    precondition(abs(color.redComponent - 10.0 / 255) < 0.001)
    let fixture = VStack {
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
    .padding(OpenMaskitTokens.spaceLg).frame(width: 600)
    .foregroundStyle(OpenMaskitTheme.text).background(OpenMaskitTheme.root)
    .preferredColorScheme(.dark)
    let view = NSHostingView(rootView: fixture)
    let size = view.fittingSize
    precondition(abs(size.width - 600) <= 1 && size.height > 90 && size.height < 300)
    view.frame = NSRect(origin: .zero, size: size)
    view.layoutSubtreeIfNeeded()
    let bitmap = view.bitmapImageRepForCachingDisplay(in: view.bounds)!
    view.cacheDisplay(in: view.bounds, to: bitmap)
    precondition(bitmap.pixelsWide > 0 && bitmap.pixelsHigh > 0)
    if CommandLine.arguments.count > 1 {
      try! bitmap.representation(using: .png, properties: [:])!
        .write(to: URL(fileURLWithPath: CommandLine.arguments[1]))
    }
    print("Native colors, aliases, components and bounded layout passed.")
  }
}
