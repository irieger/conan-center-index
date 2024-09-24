from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

import os

required_conan_version = ">=1.53.0"

class HalideConanfile(ConanFile):
    name = "halide"
    description = "A language for fast, portable computation on images and tensors"
    license = "TODO"
    homepage = "https://halide-lang.org/"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("halide", "dsl", "llvm")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        # "with_executables": [True, False],
        # "with_tiff": [True, False],
        # "with_stream_expand_tool": [True, False],
        # "disable_simd": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        # "with_executables": True,
        # "with_tiff": True,
        # "with_stream_expand_tool": False,
        # "disable_simd": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("llvm-core/13.0.0")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 17)

        # TODO: Needs some compiler checks, see list on github corresponding to a
        # specific version of halide
        # if self.settings.compiler == "gcc" and \
        #     Version(self.settings.compiler.version) < "6.0":
        #     raise ConanInvalidConfiguration(f"{self.ref} requires gcc >= 6.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        # Todo: Which options do we want to expose?
        tc.variables["WITH_TESTS"] = False
        tc.variables["WITH_TUTORIALS"] = False
        tc.variables["WITH_PYTHON_BINDINGS"] = False

        # Workaround for Conan 1 where the CXX standard version isn't set to a fallback to gnu98 happens
        if not self.settings.get_safe("compiler.cppstd"):
            tc.cache_variables["CMAKE_CXX_STANDARD"] = 14 if self.options.with_stream_expand_tool else 11

        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        self._patch_sources()

        cm = CMake(self)
        cm.configure()
        cm.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        cm = CMake(self)
        cm.install()

        # Cleanup package own pkgconfig
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "halide")
        self.cpp_info.set_property("cmake_target_name", "halide::halide")
        self.cpp_info.set_property("pkg_config_name", "halide")

        # version_suffix = ""
        # if is_msvc(self):
        #     v = Version(self.version)
        #     version_suffix = f".{v.major}.{v.minor}"
        # self.cpp_info.libs = ["openjph" + version_suffix]

        # TODO: to remove in conan v2 once cmake_find_package_* & pkg_config generators removed
        self.cpp_info.names["cmake_find_package"] = "halide"
        self.cpp_info.names["cmake_find_package_multi"] = "halide"
        self.cpp_info.names["pkg_config"] = "halide"
