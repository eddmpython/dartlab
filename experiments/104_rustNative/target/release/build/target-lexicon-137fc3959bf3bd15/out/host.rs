
#[allow(unused_imports)]
use crate::Aarch64Architecture::*;
#[allow(unused_imports)]
use crate::ArmArchitecture::*;
#[allow(unused_imports)]
use crate::CustomVendor;
#[allow(unused_imports)]
use crate::Mips32Architecture::*;
#[allow(unused_imports)]
use crate::Mips64Architecture::*;
#[allow(unused_imports)]
use crate::Riscv32Architecture::*;
#[allow(unused_imports)]
use crate::Riscv64Architecture::*;
#[allow(unused_imports)]
use crate::X86_32Architecture::*;

/// The `Triple` of the current host.
pub const HOST: Triple = Triple {
    architecture: Architecture::X86_64,
    vendor: Vendor::Pc,
    operating_system: OperatingSystem::Windows,
    environment: Environment::Msvc,
    binary_format: BinaryFormat::Coff,
};

impl Architecture {
    /// Return the architecture for the current host.
    pub const fn host() -> Self {
        Architecture::X86_64
    }
}

impl Vendor {
    /// Return the vendor for the current host.
    pub const fn host() -> Self {
        Vendor::Pc
    }
}

impl OperatingSystem {
    /// Return the operating system for the current host.
    pub const fn host() -> Self {
        OperatingSystem::Windows
    }
}

impl Environment {
    /// Return the environment for the current host.
    pub const fn host() -> Self {
        Environment::Msvc
    }
}

impl BinaryFormat {
    /// Return the binary format for the current host.
    pub const fn host() -> Self {
        BinaryFormat::Coff
    }
}

impl Triple {
    /// Return the triple for the current host.
    pub const fn host() -> Self {
        Self {
            architecture: Architecture::X86_64,
            vendor: Vendor::Pc,
            operating_system: OperatingSystem::Windows,
            environment: Environment::Msvc,
            binary_format: BinaryFormat::Coff,
        }
    }
}
