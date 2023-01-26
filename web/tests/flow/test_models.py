import pytest

from web.models import Process


@pytest.mark.django_db
def test_downcast_unknown():
    p = Process(process_type="blaa")

    with pytest.raises(NotImplementedError, match="Unknown process_type blaa"):
        p.get_specific_model()
