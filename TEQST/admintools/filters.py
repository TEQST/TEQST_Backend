import more_admin_filters

class FixedMultiSelectRelatedFilter(more_admin_filters.MultiSelectRelatedFilter):

    def has_output(self):
        if self.include_empty_choice:
            extra = 1
        else:
            extra = 0
        return len(self.lookup_choices) + extra > 1


class FixedMultiSelectRelatedDropdownFilter(more_admin_filters.MultiSelectRelatedDropdownFilter):

    def has_output(self):
        if self.include_empty_choice:
            extra = 1
        else:
            extra = 0
        return len(self.lookup_choices) + extra > 1