#
# This file is part of pretix (Community Edition).
#
# Copyright (C) 2014-2020 Raphael Michel and contributors
# Copyright (C) 2020-2021 rami.io GmbH and contributors
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General
# Public License as published by the Free Software Foundation in version 3 of the License.
#
# ADDITIONAL TERMS APPLY: Pursuant to Section 7 of the GNU Affero General Public License, additional terms are
# applicable granting you additional permissions and placing additional restrictions on your usage of this software.
# Please refer to the pretix LICENSE file to obtain the full terms applicable to this work. If you did not receive
# this file, see <https://pretix.eu/about/en/license>.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License along with this program.  If not, see
# <https://www.gnu.org/licenses/>.
#
import copy
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils.timezone import now
from django_scopes import scopes_disabled

from pretix.base.models import Discount, Event, Organizer
from pretix.base.services.pricing import apply_discounts


@pytest.fixture
def event():
    o = Organizer.objects.create(name='Dummy', slug='dummy')
    event = Event.objects.create(
        organizer=o, name='Dummy', slug='dummy',
        date_from=now()
    )
    return event


@pytest.fixture
def item(event):
    return event.items.create(name='Ticket', default_price=Decimal('23.00'))


@pytest.fixture
def item2(event):
    return event.items.create(name='Ticket II', default_price=Decimal('50.00'))


@pytest.fixture
def item3(event):
    return event.items.create(name='Ticket III', default_price=Decimal('42.00'))


@pytest.fixture
def voucher(event):
    return event.vouchers.create()


@pytest.fixture
def subevent(event):
    event.has_subevents = True
    event.save()
    return event.subevents.create(name='Foobar', date_from=now())


mixed_min_count_matching_percent = (
    Discount(
        subevent_mode=Discount.SUBEVENT_MODE_MIXED,
        condition_min_count=3,
        benefit_discount_matching_percent=20
    ),
)
mixed_min_count_one_free = (
    Discount(
        subevent_mode=Discount.SUBEVENT_MODE_MIXED,
        condition_min_count=3,
        benefit_discount_matching_percent=100,
        benefit_only_apply_to_cheapest_n_matches=1,
    ),
)
mixed_min_value_matching_percent = (
    Discount(
        subevent_mode=Discount.SUBEVENT_MODE_MIXED,
        condition_min_value=500,
        benefit_discount_matching_percent=20
    ),
)
same_min_count_matching_percent = (
    Discount(
        subevent_mode=Discount.SUBEVENT_MODE_SAME,
        condition_min_count=3,
        benefit_discount_matching_percent=20
    ),
)
same_min_count_one_free = (
    Discount(
        subevent_mode=Discount.SUBEVENT_MODE_SAME,
        condition_min_count=3,
        benefit_discount_matching_percent=100,
        benefit_only_apply_to_cheapest_n_matches=1,
    ),
)
same_min_value_matching_percent = (
    Discount(
        subevent_mode=Discount.SUBEVENT_MODE_SAME,
        condition_min_value=500,
        benefit_discount_matching_percent=20
    ),
)
distinct_min_count_matching_percent = (
    Discount(
        subevent_mode=Discount.SUBEVENT_MODE_DISTINCT,
        condition_min_count=3,
        benefit_discount_matching_percent=20
    ),
)
distinct_min_count_one_free = (
    Discount(
        subevent_mode=Discount.SUBEVENT_MODE_DISTINCT,
        condition_min_count=3,
        benefit_discount_matching_percent=100,
        benefit_only_apply_to_cheapest_n_matches=1,
    ),
)
distinct_min_count_two_free = (
    Discount(
        subevent_mode=Discount.SUBEVENT_MODE_DISTINCT,
        condition_min_count=3,
        benefit_discount_matching_percent=100,
        benefit_only_apply_to_cheapest_n_matches=2,
    ),
)


testcases_single_rule = [
    # mixed + min_count + matching_percent
    (
        mixed_min_count_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ) * 2,
        (
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        mixed_min_count_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ) * 3,
        (
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
        )
    ),
    (
        mixed_min_count_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
        )
    ),

    # mixed + min_count + matching_percent + apply_to_cheapest
    (
        mixed_min_count_one_free,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ) * 2,
        (
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        mixed_min_count_one_free,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ) * 3,
        (
            Decimal('0.00'),
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        mixed_min_count_one_free,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ) * 5,
        (
            Decimal('0.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        mixed_min_count_one_free,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ) * 6,
        (
            Decimal('0.00'),
            Decimal('0.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        mixed_min_count_one_free,
        (
            (1, 1, now(), Decimal('1.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('2.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('3.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('4.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('5.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('6.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('0.00'),
            Decimal('0.00'),
            Decimal('3.00'),
            Decimal('4.00'),
            Decimal('5.00'),
            Decimal('6.00'),
        )
    ),

    # mixed + min_value + matching_percent
    (
        mixed_min_value_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ) * 4,
        (
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        mixed_min_value_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ) * 5,
        (
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
        )
    ),
    (
        mixed_min_value_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ) * 10,
        (
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
        )
    ),

    # same + min_count + matching_percent
    (
        same_min_count_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        same_min_count_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        same_min_count_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('120.00'),
        )
    ),

    # same + min_count + matching_percent + apply_to_cheapest
    (
        same_min_count_one_free,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('0.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('0.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        same_min_count_one_free,
        (
            (1, 1, now(), Decimal('1.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('2.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('3.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('4.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('5.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('6.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('7.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('8.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('9.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('0.00'),
            Decimal('2.00'),
            Decimal('3.00'),
            Decimal('0.00'),
            Decimal('5.00'),
            Decimal('6.00'),
            Decimal('7.00'),
            Decimal('8.00'),
            Decimal('9.00'),
        )
    ),

    # same + min_value + matching_percent
    (
        same_min_value_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
        )
    ),

    # distinct + min_count + matching_percent
    (
        distinct_min_count_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        distinct_min_count_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
        )
    ),
    (
        distinct_min_count_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        distinct_min_count_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 4, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
        )
    ),
    (
        distinct_min_count_matching_percent,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 4, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('96.00'),
            Decimal('120.00'),
        )
    ),

    # distinct + min_count + matching_percent + apply_to_cheapest
    (
        distinct_min_count_one_free,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        distinct_min_count_one_free,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('0.00'),
            Decimal('120.00'),
            Decimal('120.00'),
        )
    ),
    (
        distinct_min_count_one_free,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 4, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('0.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('0.00'),
        )
    ),
    (
        distinct_min_count_one_free,
        (
            (1, 1, now(), Decimal('3.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('2.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('1.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('1.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('2.00'), False, False, Decimal('0.00')),
            (1, 4, now(), Decimal('3.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('3.00'),
            Decimal('2.00'),
            Decimal('0.00'),
            Decimal('0.00'),
            Decimal('2.00'),
            Decimal('3.00'),
        )
    ),
    (
        distinct_min_count_two_free,
        (
            (1, 1, now(), Decimal('3.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('2.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('1.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('1.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('2.00'), False, False, Decimal('0.00')),
            (1, 4, now(), Decimal('3.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('3.00'),
            Decimal('0.00'),
            Decimal('0.00'),
            Decimal('0.00'),
            Decimal('0.00'),
            Decimal('3.00'),
        )
    ),
    (
        distinct_min_count_one_free,
        (
            (1, 1, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 4, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 5, now(), Decimal('120.00'), False, False, Decimal('0.00')),
            (1, 6, now(), Decimal('120.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('0.00'),
            Decimal('120.00'),
            Decimal('120.00'),
            Decimal('0.00'),
        )
    ),
    (
        distinct_min_count_one_free,
        (
            (1, 1, now(), Decimal('1.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('2.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('3.00'), False, False, Decimal('0.00')),
            (1, 4, now(), Decimal('4.00'), False, False, Decimal('0.00')),
            (1, 5, now(), Decimal('5.00'), False, False, Decimal('0.00')),
            (1, 6, now(), Decimal('6.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('0.00'),
            Decimal('0.00'),
            Decimal('3.00'),
            Decimal('4.00'),
            Decimal('5.00'),
            Decimal('6.00'),
        )
    ),
    (
        distinct_min_count_one_free,
        (
            (1, 1, now(), Decimal('4.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('4.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('4.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('6.00'), False, False, Decimal('0.00')),
            (1, 2, now(), Decimal('6.00'), False, False, Decimal('0.00')),
            (1, 3, now(), Decimal('6.00'), False, False, Decimal('0.00')),
        ),
        (
            # This one is unexpected, since the customer could get a lower price
            # if they would split their order, but it's not really possible to solve
            # that without giving up other desired effects.
            Decimal('0.00'),
            Decimal('0.00'),
            Decimal('4.00'),
            Decimal('6.00'),
            Decimal('6.00'),
            Decimal('6.00'),
        )
    ),

    # Unconditional
    (
        (
            Discount(condition_min_count=1, benefit_discount_matching_percent=20),
        ),
        (
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('80.00'),
        )
    ),
    (
        (
            Discount(
                condition_min_count=1,
                benefit_discount_matching_percent=100,
                benefit_only_apply_to_cheapest_n_matches=1
            ),
        ),
        (
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('0.00'),
            Decimal('0.00'),
        )
    ),

    # Apply partial discount to partial items
    (
        (
            Discount(
                condition_min_count=3,
                benefit_discount_matching_percent=20,
                benefit_only_apply_to_cheapest_n_matches=2
            ),
        ),
        (
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('100.00'),
            Decimal('80.00'),
            Decimal('80.00'),
        )
    ),

    # Addon handling
    (
        (
            Discount(
                condition_min_count=3,
                benefit_discount_matching_percent=20,
            ),
        ),
        (
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), True, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), True, False, Decimal('0.00')),
        ),
        (
            Decimal('80.00'),
            Decimal('80.00'),
            Decimal('80.00'),
        )
    ),
    (
        (
            Discount(
                condition_min_count=3,
                benefit_discount_matching_percent=20,
                condition_apply_to_addons=False,
            ),
        ),
        (
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), True, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), True, False, Decimal('0.00')),
        ),
        (
            Decimal('80.00'),
            Decimal('80.00'),
            Decimal('80.00'),
            Decimal('100.00'),
            Decimal('100.00'),
        )
    ),
    (
        (
            Discount(
                condition_min_count=3,
                benefit_discount_matching_percent=20,
                condition_apply_to_addons=False,
            ),
        ),
        (
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), True, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), True, False, Decimal('0.00')),
        ),
        (
            Decimal('100.00'),
            Decimal('100.00'),
            Decimal('100.00'),
        )
    ),

    # Ignore bundled
    (
        (
            Discount(
                condition_min_count=3,
                benefit_discount_matching_percent=20,
                condition_apply_to_addons=False,
            ),
        ),
        (
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), True, True, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), True, True, Decimal('0.00')),
        ),
        (
            Decimal('100.00'),
            Decimal('100.00'),
            Decimal('100.00'),
        )
    ),
]


testcases_multiple_rules = [
    # min_count consumes all discounted
    (
        (
            Discount(
                condition_min_count=2,
                benefit_discount_matching_percent=20,
            ),
            Discount(
                condition_min_count=1,
                benefit_discount_matching_percent=50,
            ),
        ),
        (
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('80.00'),
            Decimal('80.00'),
            Decimal('80.00'),
        )
    ),
    # reordered
    (
        (
            Discount(
                condition_min_count=1,
                benefit_discount_matching_percent=50,
                position=2,
            ),
            Discount(
                condition_min_count=2,
                benefit_discount_matching_percent=20,
                position=1,
            ),
        ),
        (
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('80.00'),
            Decimal('80.00'),
            Decimal('80.00'),
        )
    ),
    # min_count does not consume uneven numbers if not required
    (
        (
            Discount(
                condition_min_count=2,
                benefit_discount_matching_percent=20,
                benefit_only_apply_to_cheapest_n_matches=1
            ),
            Discount(
                condition_min_count=1,
                benefit_discount_matching_percent=50,
            ),
        ),
        (
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('100.00'),
            Decimal('80.00'),
            Decimal('50.00'),
        )
    ),
    (
        (
            Discount(
                condition_min_count=2,
                benefit_discount_matching_percent=20,
                benefit_only_apply_to_cheapest_n_matches=1
            ),
            Discount(
                condition_min_count=1,
                benefit_discount_matching_percent=50,
            ),
        ),
        (
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('100.00'),
            Decimal('80.00'),
            Decimal('100.00'),
            Decimal('80.00'),
            Decimal('50.00'),
        )
    ),
    # min_value consumes all matching
    (
        (
            Discount(
                condition_min_value=Decimal('5.00'),
                benefit_discount_matching_percent=20,
            ),
            Discount(
                condition_min_count=1,
                benefit_discount_matching_percent=50,
            ),
        ),
        (
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
            (1, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
        ),
        (
            Decimal('80.00'),
            Decimal('80.00'),
            Decimal('80.00'),
        )
    ),
]


@pytest.mark.parametrize("discounts,positions,expected", testcases_single_rule + testcases_multiple_rules)
@pytest.mark.django_db
@scopes_disabled()
def test_discount_evaluation(event, item, subevent, discounts, positions, expected):
    for d in discounts:
        d = copy.copy(d)
        d.event = event
        d.internal_name = 'Discount'
        d.full_clean()
        d.save()
    new_prices = [p for p, d in apply_discounts(event, 'web', positions)]
    assert sorted(new_prices) == sorted(expected)


@pytest.mark.django_db
@scopes_disabled()
def test_limit_products(event, item, item2):
    d1 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=20, condition_all_products=False)
    d1.save()
    d1.condition_limit_products.add(item2)
    d2 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=50, condition_all_products=True)
    d2.save()

    positions = (
        (item.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
    )
    expected = (
        Decimal('80.00'),
        Decimal('80.00'),
        Decimal('50.00'),
        Decimal('50.00'),
    )

    new_prices = [p for p, d in apply_discounts(event, 'web', positions)]
    assert sorted(new_prices) == sorted(expected)


@pytest.mark.django_db
@scopes_disabled()
def test_limit_products_subevents_distinct(event, item, item2):
    d1 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=20, condition_all_products=False,
                  subevent_mode=Discount.SUBEVENT_MODE_DISTINCT)
    d1.save()
    d1.condition_limit_products.add(item)

    positions = (
        (item.pk, 1, now(), Decimal('100.00'), False, False, Decimal('0.00')),
        (item.pk, 2, now(), Decimal('100.00'), False, False, Decimal('0.00')),
        (item.pk, 3, now(), Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, 4, now(), Decimal('50.00'), False, False, Decimal('0.00')),
    )
    expected = (
        Decimal('80.00'),
        Decimal('80.00'),
        Decimal('80.00'),
        Decimal('50.00'),
    )

    new_prices = [p for p, d in apply_discounts(event, 'web', positions)]
    assert sorted(new_prices) == sorted(expected)


@pytest.mark.django_db
@scopes_disabled()
def test_sales_channels(event, item):
    d1 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=20, all_sales_channels=False)
    d1.save()
    d1.limit_sales_channels.add(event.organizer.sales_channels.get(identifier="bar"))
    d2 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=50, all_sales_channels=False)
    d2.save()
    d2.limit_sales_channels.add(event.organizer.sales_channels.get(identifier="web"))
    d2.limit_sales_channels.add(event.organizer.sales_channels.get(identifier="bar"))

    positions = (
        (item.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
    )

    assert sorted([p for p, d in apply_discounts(event, 'bar', positions)]) == [Decimal('80.00'), Decimal('80.00')]
    assert sorted([p for p, d in apply_discounts(event, 'web', positions)]) == [Decimal('50.00'), Decimal('50.00')]


@pytest.mark.django_db
@scopes_disabled()
def test_available_from(event, item):
    d1 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=20, available_from=now() + timedelta(days=1))
    d1.save()
    d2 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=50, available_from=now() - timedelta(days=1))
    d2.save()

    positions = (
        (item.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
    )

    assert sorted([p for p, d in apply_discounts(event, 'web', positions)]) == [Decimal('50.00'), Decimal('50.00')]


@pytest.mark.django_db
@scopes_disabled()
def test_available_until(event, item):
    d1 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=20, available_until=now() - timedelta(days=1))
    d1.save()
    d2 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=50, available_until=now() + timedelta(days=1))
    d2.save()

    positions = (
        (item.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
    )

    assert sorted([p for p, d in apply_discounts(event, 'web', positions)]) == [Decimal('50.00'), Decimal('50.00')]


@pytest.mark.django_db
@scopes_disabled()
def test_subevent_date_from(event, item, subevent):
    subevent_date = subevent.date_from  # prevent test timing errors
    d1 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=20,
                  subevent_date_from=subevent_date + timedelta(days=1))
    d1.save()
    d2 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=50,
                  subevent_date_from=subevent_date)
    d2.save()

    # (item_id, subevent_id, subevent_date_from, line_price_gross, is_addon_to, is_bundled, voucher_discount)
    positions = (
        (item.pk, subevent.pk, subevent.date_from, Decimal('100.00'), False, False, Decimal('0.00')),
        (item.pk, subevent.pk, subevent.date_from, Decimal('100.00'), False, False, Decimal('0.00')),
    )

    assert sorted([p for p, d in apply_discounts(event, 'web', positions)]) == [Decimal('50.00'), Decimal('50.00')]


@pytest.mark.django_db
@scopes_disabled()
def test_subevent_date_until(event, item, subevent):
    subevent_date = subevent.date_from  # prevent test timing errors
    d1 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=50,
                  subevent_date_until=subevent_date - timedelta(seconds=1))
    d1.save()
    d2 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=20,
                  subevent_date_until=subevent_date + timedelta(days=1))
    d2.save()

    # (item_id, subevent_id, subevent_date_from, line_price_gross, is_addon_to, is_bundled, voucher_discount)
    positions = (
        (item.pk, subevent.pk, subevent.date_from, Decimal('100.00'), False, False, Decimal('0.00')),
        (item.pk, subevent.pk, subevent.date_from, Decimal('100.00'), False, False, Decimal('0.00')),
    )

    assert sorted([p for p, d in apply_discounts(event, 'web', positions)]) == [Decimal('80.00'), Decimal('80.00')]


@pytest.mark.django_db
@scopes_disabled()
def test_subevent_date_from_until(event, item, subevent):
    subevent_date = subevent.date_from  # prevent test timing errors
    d1 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=20,
                  subevent_date_from=subevent_date + timedelta(days=1),
                  subevent_date_until=subevent_date + timedelta(days=2))
    d1.save()
    d2 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=50,
                  subevent_date_from=subevent_date - timedelta(days=2),
                  subevent_date_until=subevent_date - timedelta(days=1))
    d2.save()
    d3 = Discount(event=event, condition_min_count=2, benefit_discount_matching_percent=80,
                  subevent_date_from=subevent_date, subevent_date_until=subevent_date + timedelta(days=1))
    d3.save()

    # (item_id, subevent_id, subevent_date_from, line_price_gross, is_addon_to, is_bundled, voucher_discount)
    positions = (
        (item.pk, subevent.pk, subevent.date_from, Decimal('100.00'), False, False, Decimal('0.00')),
        (item.pk, subevent.pk, subevent.date_from, Decimal('100.00'), False, False, Decimal('0.00')),
    )

    assert sorted([p for p, d in apply_discounts(event, 'web', positions)]) == [Decimal('20.00'), Decimal('20.00')]


@pytest.mark.django_db
@scopes_disabled()
def test_discount_other_products_min_count(event, item, item2):
    # "For every 5 item2, one item1 gets in for free"
    d1 = Discount(
        event=event,
        condition_min_count=5,
        condition_all_products=False,
        benefit_discount_matching_percent=100,
        benefit_only_apply_to_cheapest_n_matches=1,
        benefit_same_products=False,
    )
    d1.save()
    d1.condition_limit_products.add(item2)
    d1.benefit_limit_products.add(item)

    positions = (
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('90.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('90.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('90.00'), False, False, Decimal('0.00')),
    )
    expected = (
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('90.00'),
        Decimal('0.00'),
        Decimal('0.00'),
    )

    new_prices = [p for p, d in apply_discounts(event, 'web', positions)]
    assert sorted(new_prices) == sorted(expected)


@pytest.mark.django_db
@scopes_disabled()
def test_discount_other_products_min_count_no_addon(event, item, item2):
    # "For every 2 item2, one item1 gets in for free, but no addons"
    d1 = Discount(
        event=event,
        condition_min_count=2,
        condition_all_products=False,
        benefit_discount_matching_percent=100,
        benefit_only_apply_to_cheapest_n_matches=1,
        benefit_same_products=False,
        benefit_apply_to_addons=False,
    )
    d1.save()
    d1.condition_limit_products.add(item2)
    d1.benefit_limit_products.add(item)

    positions = (
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('90.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('90.00'), True, False, Decimal('0.00')),
    )
    expected = (
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('90.00'),
        Decimal('0.00'),
    )

    new_prices = [p for p, d in apply_discounts(event, 'web', positions)]
    assert sorted(new_prices) == sorted(expected)


@pytest.mark.django_db
@scopes_disabled()
def test_discount_other_products_min_count_no_voucher(event, item, item2):
    # "For every 2 item2, one item1 gets in for free, but no discount on already discounted"
    d1 = Discount(
        event=event,
        condition_min_count=2,
        condition_all_products=False,
        benefit_discount_matching_percent=100,
        benefit_only_apply_to_cheapest_n_matches=1,
        benefit_same_products=False,
        benefit_ignore_voucher_discounted=True,
    )
    d1.save()
    d1.condition_limit_products.add(item2)
    d1.benefit_limit_products.add(item)

    positions = (
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('40.00'), False, False, Decimal('50.00')),
        (item.pk, None, None, Decimal('40.00'), False, False, Decimal('50.00')),
        (item.pk, None, None, Decimal('90.00'), False, False, Decimal('0.00')),
    )
    expected = (
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('40.00'),
        Decimal('40.00'),
        Decimal('0.00'),
    )

    new_prices = [p for p, d in apply_discounts(event, 'web', positions)]
    assert sorted(new_prices) == sorted(expected)


@pytest.mark.django_db
@scopes_disabled()
def test_discount_subgroup_cheapest_n_min_count(event, item, item2):
    # "For every 4 products, you get one free, but only of type item"
    d1 = Discount(
        event=event,
        condition_min_count=4,
        condition_all_products=False,
        benefit_discount_matching_percent=100,
        benefit_only_apply_to_cheapest_n_matches=1,
        benefit_same_products=False,
    )
    d1.save()
    d1.condition_limit_products.add(item)
    d1.condition_limit_products.add(item2)
    d1.benefit_limit_products.add(item)

    positions = (
        # 11 items of item2, which contribute to the total count of 15, but do not get reduced
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('100.00'), False, False, Decimal('0.00')),
        # 4 items of item, of which 3 of the cheapest will be reduced
        (item.pk, None, None, Decimal('110.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('110.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('90.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('90.00'), False, False, Decimal('0.00')),
    )
    expected = (
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('100.00'),
        Decimal('110.00'),
        Decimal('0.00'),
        Decimal('0.00'),
        Decimal('0.00'),
    )

    new_prices = [p for p, d in apply_discounts(event, 'web', positions)]
    assert sorted(new_prices) == sorted(expected)


@pytest.mark.django_db
@scopes_disabled()
def test_discount_other_products_min_value(event, item, item2):
    # "If you buy item1 for at least €99, you get all item2 for 20% off"
    d1 = Discount(
        event=event,
        condition_min_value=99,
        condition_all_products=False,
        benefit_discount_matching_percent=20,
        benefit_same_products=False,
    )
    d1.save()
    d1.condition_limit_products.add(item)
    d1.benefit_limit_products.add(item2)

    positions = (
        (item.pk, None, None, Decimal('50.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('23.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('23.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('23.00'), False, False, Decimal('0.00')),
    )
    expected = (
        Decimal('50.00'),
        Decimal('23.00'),
        Decimal('23.00'),
        Decimal('23.00'),
    )

    new_prices = [p for p, d in apply_discounts(event, 'web', positions)]
    assert sorted(new_prices) == sorted(expected)

    positions = (
        (item.pk, None, None, Decimal('50.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('50.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('23.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('23.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('23.00'), False, False, Decimal('0.00')),
    )
    expected = (
        Decimal('50.00'),
        Decimal('50.00'),
        Decimal('18.40'),
        Decimal('18.40'),
        Decimal('18.40'),
    )

    new_prices = [p for p, d in apply_discounts(event, 'web', positions)]
    assert sorted(new_prices) == sorted(expected)


@pytest.mark.django_db
@scopes_disabled()
def test_multiple_discounts_with_benefit_condition_overlap(event, item, item2):
    # "For every 5 item2, you get one item1 for 20 % off." + "For every two item1, you get one 10% off."
    d1 = Discount(
        event=event,
        condition_min_count=5,
        condition_all_products=False,
        benefit_only_apply_to_cheapest_n_matches=1,
        benefit_discount_matching_percent=20,
        benefit_same_products=False,
        position=1,
    )
    d1.save()
    d1.condition_limit_products.add(item2)
    d1.benefit_limit_products.add(item)

    d2 = Discount(
        event=event,
        condition_min_count=2,
        condition_all_products=False,
        benefit_only_apply_to_cheapest_n_matches=1,
        benefit_discount_matching_percent=10,
        benefit_same_products=True,
        position=2,
    )
    d2.save()
    d2.condition_limit_products.add(item)

    positions = (
        (item2.pk, None, None, Decimal('50.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('50.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('50.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('50.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('50.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('50.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('23.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('23.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('23.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('23.00'), False, False, Decimal('0.00')),
    )
    expected = (
        # item2 remains untouched
        Decimal('50.00'),
        Decimal('50.00'),
        Decimal('50.00'),
        Decimal('50.00'),
        Decimal('50.00'),
        Decimal('50.00'),
        # one item is reduced 20% because we have >5 item2
        Decimal('18.40'),
        # one item is reduced 10% because it's part of a group of two
        Decimal('20.70'),
        # two remain full price
        Decimal('23.00'),
        Decimal('23.00'),
    )

    new_prices = [p for p, d in apply_discounts(event, 'web', positions)]
    assert sorted(new_prices) == sorted(expected)


@pytest.mark.django_db
@scopes_disabled()
def test_multiple_discounts_with_same_condition(event, item, item2, item3):
    # "For every 1 item1, you get three item2 for 10 % off." + "For every 1 item1, you get five item3 for 10 % off."
    d1 = Discount(
        event=event,
        condition_min_count=1,
        condition_all_products=False,
        benefit_only_apply_to_cheapest_n_matches=3,
        benefit_discount_matching_percent=10,
        benefit_same_products=False,
        position=1,
    )
    d1.save()
    d1.condition_limit_products.add(item)
    d1.benefit_limit_products.add(item2)

    d2 = Discount(
        event=event,
        condition_min_count=1,
        condition_all_products=False,
        benefit_only_apply_to_cheapest_n_matches=5,
        benefit_discount_matching_percent=10,
        benefit_same_products=False,
        position=2,
    )
    d2.save()
    d2.condition_limit_products.add(item)
    d2.benefit_limit_products.add(item3)

    positions = (
        (item3.pk, None, None, Decimal('42.00'), False, False, Decimal('0.00')),
        (item3.pk, None, None, Decimal('42.00'), False, False, Decimal('0.00')),
        (item3.pk, None, None, Decimal('42.00'), False, False, Decimal('0.00')),
        (item3.pk, None, None, Decimal('42.00'), False, False, Decimal('0.00')),
        (item3.pk, None, None, Decimal('42.00'), False, False, Decimal('0.00')),
        (item3.pk, None, None, Decimal('42.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('50.00'), False, False, Decimal('0.00')),
        (item2.pk, None, None, Decimal('50.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('23.00'), False, False, Decimal('0.00')),
        (item.pk, None, None, Decimal('23.00'), False, False, Decimal('0.00')),
    )
    expected = (
        # both item1 remain full price
        Decimal('23.00'),
        Decimal('23.00'),
        # 5 item3 discounted
        Decimal('37.80'),
        Decimal('37.80'),
        Decimal('37.80'),
        Decimal('37.80'),
        Decimal('37.80'),
        # 2 item2 discounted
        Decimal('45.00'),
        Decimal('45.00'),
        # 1 item3 remains untouched
        Decimal('42.00'),
    )

    new_prices = [p for p, d in apply_discounts(event, 'web', positions)]
    assert sorted(new_prices) == sorted(expected)
