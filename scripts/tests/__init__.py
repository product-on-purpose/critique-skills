# what-it-is:   the package marker for scripts/tests/
# what-it-does: nothing at runtime; makes the repo-tooling test modules a package
# why:          keeps their module names distinct from same-named test modules
#               elsewhere in the tree, which pytest would otherwise reject
# used-by:      pytest collection
